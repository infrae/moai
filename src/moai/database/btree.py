import time
import datetime
import bsddb

from zope.interface import implements

from moai.interfaces import IDatabase

class BTreeDatabase(object):
    implements(IDatabase)

    def __init__(self, dbpath=None, mode='w'):

        if dbpath is None:
            self._content = bsddb.hashopen(dbpath, mode)
            self._sets = bsddb.hashopen(dbpath, mode)
            self._dates = bsddb.btopen(dbpath, mode)
        else:
            self._content = bsddb.hashopen(dbpath + '_content.db', mode)
            self._sets = bsddb.hashopen(dbpath + '_sets.db', mode)
            self._dates = bsddb.btopen(dbpath + '_dates.db', mode)

    def _datetime2key(self, datetime):
        return '%0.10d' % time.mktime(datetime.timetuple())

    def _key2datetime(self, key):
        return datetime.datetime(*time.gmtime(int(key))[:6])

    def get_record(self, id):
        return eval(self._content[id.encode('utf8')])['record']
                
    def get_metadata(self, id):
        return eval(self._content[id.encode('utf8')])['metadata']

    def get_assets(self, id):
        return eval(self_content[id.encode('utf8')])['assets']

    def get_set(self, id):
        return eval(self._sets[id.encode('utf8')])

    def remove_content(self, id):
        id = id.encode('utf8')
        data = eval(self._content.get(id))
        if data is None:
            return False
        datestamp = self._datetime2key(data['record']['when_modified'])
        del self._dates[datestamp]
        sets = eval(self._content[id])['sets']
        del self._content[id]
        for set in sets:
            set = set.encode('utf8')
            self._sets[set] = unicode(eval(self._sets[set])['content'].remove(id))
        return True
    
    def add_content(self, id, sets, record_data, meta_data, assets_data):
        datestamp =  self._datetime2key(record_data['when_modified'])
        id = id.encode('utf8')
        self._dates[datestamp]=id
        self._content[id]= unicode({'record':record_data,
                                    'metadata':meta_data,
                                    'assets':assets_data,
                                    'sets':sets})
        for set in sets:
            set_id = set.encode('utf8')
            if not self._sets.has_key(set_id):
                self._sets[set_id] = unicode({'id':set,
                                              'name':set,
                                              'description':None,
                                              'content':[]})
            data = eval(self._sets[set_id])
            if id not in data['content']:
                data['content'].append(id)
            self._sets[set_id] = unicode(data)
        return True

    def add_set(self, set_id, name, description=None):
        id = set_id.encode('utf8')
        if not self._sets.has_key(id):
            self._sets[id] = unicode({'content':[]})
        data = eval(self._sets[id])
        data['id'] = set_id
        data['name'] = name
        if description:
            data['description'] = description
        else:
            data['description'] = None
            
        self._sets[id.encode('utf8')] = unicode(data)

    def remove_set(self, id):
        data = eval(self._sets[id.encode('utf8')])
        del self._sets[id.encode('utf8')]
        for cid in data['content']:
            cid = cid.encode('utf8')
            self._content[cid] = eval(self._content[cid])['sets'].remove(id)

    def oai_sets(self, offset=0, batch_size=20):
        ids = self._sets.keys()[offset:offset+batch_size]
        for id in ids:
            result = eval(self._sets[id]).copy()
            del result['content']
            yield result

    def oai_query(self,
                  offset=0,
                  batch_size=20,
                  sets=[],
                  not_sets=[],
                  filter_sets=[],
                  from_date=None,
                  until_date=None,
                  identifier=None):

        if len(self._dates) == 0:
            yield
            return

        # make sure until date is set, and not in future
        if until_date == None or until_date > datetime.datetime.now():
            until_date = datetime.datetime.now()

        # make sure from date is set
        if from_date == None:
            from_date = self._key2datetime(self._dates.first()[0])

        until_date = self._datetime2key(until_date)
        from_date = self._datetime2key(from_date)

        if from_date < self._dates.first()[0]:
            start_date = self._dates.first()[0]
        else:
             start_date = from_date

        if until_date > self._dates.last()[0]:
            stop_date = self._dates.last()[0]
        else:
            stop_date = until_date

        ids = set()
        
        # filter dates

        if start_date > self._dates.last()[0]:
            date = start_date
        else:
            date, id = self._dates.set_location(start_date)
        while date <= stop_date:
            ids.add(id)
            try:
                date, id = self._dates.next()
            except:
                break

        # filter sets

        set_ids = set()
        for set_id in sets:
            set_ids = set_ids.union(set(eval(self._sets[set_id])['content']))
        if set_ids:
            ids = ids.intersection(set_ids)

        # filter not_sets
        
        not_set_ids = set()
        for set_id in not_sets:
            not_set_ids = not_set_ids.union(set(eval(self._sets[set_id])['content']))
        if not_set_ids:
            ids = ids.difference(not_set_ids)

        # extra filter sets
        
        filter_set_ids = set()
        for set_id in filter_sets:
            filter_set_ids = filter_set_ids.union(set(eval(self._sets[set_id])['content']))
        if filter_set_ids:
            ids = ids.intersection(filter_set_ids)

        if identifier:
            yield eval(self._content[id])
            return
        
        # filter batching
        
        if batch_size < 0:
            batch_size = 0
            
        ids = list(ids)[offset:offset+batch_size]

        for id in ids:
            yield eval(self._content[id])
    
