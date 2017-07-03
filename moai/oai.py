from pkg_resources import iter_entry_points

from datetime import datetime
import pkg_resources
import time

import oaipmh
import oaipmh.metadata
import oaipmh.server
import oaipmh.error

def get_writer(prefix, config, db):
    for writer in iter_entry_points(group='moai.format', name=prefix):
        return writer.load()(prefix, config, db)
    else:
        raise ValueError('No such metadata format registered: %s' % prefix)


class OAIServer(object):
    """An OAI-2.0 compliant oai server.
    
    Underlying code is based on pyoai's oaipmh.server'
    """
    
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def identify(self):
        result = oaipmh.common.Identify(
            repositoryName=self.config.name,
            baseURL=self.config.url,
            protocolVersion='2.0',
            adminEmails=self.config.admins,
            earliestDatestamp=self.db.oai_earliest_datestamp(),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'],
            toolkit_description=False)

        version = ''
        pyoai_egg = pkg_resources.working_set.find(
            pkg_resources.Requirement.parse('pyoai'))
        moai_egg = pkg_resources.working_set.find(
            pkg_resources.Requirement.parse('MOAI'))
        
        if moai_egg and pyoai_egg:
            version = '<version>%s (using pyoai%s)</version>' % (
                moai_egg.version,
                pyoai_egg.version)
        result.add_description(
            '<toolkit xsi:schemaLocation='
            '"http://oai.dlib.vt.edu/OAI/metadata/toolkit '
            'http://oai.dlib.vt.edu/OAI/metadata/toolkit.xsd" '
            'xmlns="http://oai.dlib.vt.edu/OAI/metadata/toolkit" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<title>MOAI</title>'
            '%s'
            '<URL>http://moai.infrae.com</URL>'
            '</toolkit>' % version)
            
        return result

    def listMetadataFormats(self, identifier=None):
        result = []
        for prefix in self.config.metadata_prefixes:
            writer = get_writer(prefix, self.config, self.db)
            ns = writer.get_namespace()
            schema = writer.get_schema_location()
            result.append((prefix, schema, ns))
        return result
    
    def listSets(self, cursor=0, batch_size=20):
        for set in self.db.oai_sets(cursor, batch_size):
            yield [set['id'], set['name'], set['description']]

    def listRecords(self, metadataPrefix, set=None, from_=None, until=None,
                    cursor=0, batch_size=10):
        
        self._checkMetadataPrefix(metadataPrefix)
        for record in self._listQuery(set, from_, until, cursor, batch_size):
            header, metadata = self._createHeaderAndMetadata(record)
            yield header, metadata, None

    def listIdentifiers(self, metadataPrefix, set=None, from_=None, until=None,
                        cursor=0, batch_size=10):
        
        self._checkMetadataPrefix(metadataPrefix)
        for record in self._listQuery(set, from_, until, cursor, batch_size):
            yield self._createHeader(record)

    def getRecord(self, metadataPrefix, identifier):
        self._checkMetadataPrefix(metadataPrefix)
        header = None
        metadata = None
        for record in self._listQuery(identifier=identifier):
            header, metadata = self._createHeaderAndMetadata(record)
        if header is None:
            raise oaipmh.error.IdDoesNotExistError(identifier)
        return header, metadata, None
        
    def _checkMetadataPrefix(self, metadataPrefix):
        if metadataPrefix not in self.config.metadata_prefixes:
            raise oaipmh.error.CannotDisseminateFormatError

    def _createHeader(self, record):
        deleted = record['deleted']
        for setspec in record['sets']:
            if setspec in self.config.sets_deleted:
                deleted = True
                break
        return oaipmh.common.Header(None,
                                    record['id'],
                                    record['modified'],
                                    record['sets'],
                                    deleted)

    def _createHeaderAndMetadata(self, record):
        header = self._createHeader(record)
        metadata = oaipmh.common.Metadata(None, record)
        metadata.record = record
        return header, metadata
    
    def _listQuery(self, set=None, from_=None, until=None, 
                   cursor=0, batch_size=10, identifier=None):
            
        now = datetime.utcnow()
        if until != None and until > now:
            # until should never be in the future
            until = now
            
        if self.config.delay:
            # subtract delay from until_ param, if present
            if until is None:
                until = datetime.utcnow()
            until = until.timetuple()
            ut = time.mktime(until)-self.filter_data.delay
            until = datetime.fromtimestamp(ut)
            
        needed_sets = self.config.sets_needed.copy()
        if not set is None:
            needed_sets.add(set)
        allowed_sets = self.config.sets_allowed.copy()
        disallowed_sets = self.config.sets_disallowed.copy()    
        
        return self.db.oai_query(offset=cursor,
                                 batch_size=batch_size,
                                 needed_sets=needed_sets,
                                 disallowed_sets=disallowed_sets,
                                 allowed_sets=allowed_sets,
                                 from_date=from_,
                                 until_date=until,
                                 identifier=identifier
                                 )

def OAIServerFactory(db, config):
    """Create a new OAI batching OAI Server given a config and
    a database"""
    
    metadata_registry = oaipmh.metadata.MetadataRegistry()
    for prefix in config.metadata_prefixes:
        metadata_registry.registerWriter(prefix,
                                         get_writer(prefix, config, db))
            
    return oaipmh.server.BatchingServer(
        OAIServer(db, config),
        metadata_registry=metadata_registry,
        resumption_batch_size=config.batch_size
        )
