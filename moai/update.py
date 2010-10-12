from moai.error import ContentError, DatabaseError

class DatabaseUpdater(object):
    """Default implementation of :ref:`IDatabaseUpdater`.
    
    This class can update something implementing :ref:`IDatabase`
    given a contentprovider and content object class
    (implementations of :ref:`IContentProvider` and :ref:`IContentObject`)
    """

    def __init__(self, content, content_class, database, log, flush_threshold=-1):
        self.set_database(database)
        self.set_content_provider(content)
        self.set_content_object_class(content_class)
        self.set_logger(log)
        self.flush_threshold = flush_threshold

    def set_database(self, database):
        self.db = database

    def set_content_provider(self, content):
        self._provider = content

    def set_content_object_class(self, content_class):
        self._content_object_class = content_class

    def set_logger(self, log):
        self._log = log

    def update_provider(self, from_date=None):
        result = []
        for id in self.update_provider_iterate(from_date):
            result.append(id)
        return result
            
    def update_provider_iterate(self, from_date=None):
        msg = 'Starting the update of %s' % self._provider.__class__.__name__
        if not from_date is None:
            msg += 'from %s' % from_date
        self._log.info(msg)
        count = 0
        for id in self._provider.update(from_date):
            yield id
            count += 1
        
        self._log.info('Updating %s returned %s new/modified objects' % (
            self._provider.__class__.__name__,
            count))
            
    def update_database(self, validate=True, supress_errors=False):
        errors = 0
        for count, total, content_id, error in self.update_database_iterate(
                                                    validate, supress_errors):
            if not error is None:
                errors += 1
        return errors
    
    def update_database_iterate(self, validate=True, supress_errors=False):    
        total = self._provider.count()
        self._log.info('Updating %s with %s %s objects' % (
            self.db.__class__.__name__,
            total,
            self._content_object_class.__name__))

        count = 0
        errors = 0
        for content_id in self._provider.get_content_ids():
            # If enabled (thres > -1), flush db-cache after every X records 
            if self.flush_threshold > -1 and count > 0 and \
               count % self.flush_threshold == 0:
                try:
                    self.db.flush_update()
                except Exception, err:
                    if not supress_errors:
                        raise
            count += 1

            # First try to get the content
            try:
                content_data = self._provider.get_content_by_id(content_id)
                content = self._content_object_class()
                stop = content.update(content_data, self._provider)
                
                if stop is False:
                    self._log.info('Ignoring %s' % content_id)
                    continue
            except Exception, err:
                if not supress_errors:
                    raise

                errors += 1
                yield (count, total, content_id,
                       ContentError(self._content_object_class, content_id))
                continue

            # Not a set, compose the record
            try:
                self.db.update_record(content.id,
                                      content.modified,
                                      content.deleted,
                                      content.sets,
                                      content.data)
            except Exception:
                if not supress_errors:
                    raise
                yield count, total, content.id, DatabaseError(id, 'set')
                continue
           
            yield count, total, content.id, None

        # Always flush db-cache
        try:
            self.db.flush()
        except Exception, err:
            if not supress_errors:
                raise
