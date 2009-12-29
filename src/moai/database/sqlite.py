import time
import datetime

from zope.interface import implements
import sqlalchemy as sql

from moai.interfaces import IDatabase

class SQLiteDatabase(object):
    """Sqlite implementation of a database backend
    This implements the :ref:`IDatabase` interface, look there for
    more documentation.
    """
    implements(IDatabase)

    def __init__(self, dbpath=None, mode='w'):
        self._path = dbpath
        self.db = self._connect(dbpath)
        self.records = self.db.tables['records']
        self.metadata = self.db.tables['metadata']
        self._record_id = 0
        self._record_cache = []
        self._metadata_cache = []
        self._set_ids = set(self._get_set_ids())
    
    def _connect(self, dbpath):
        if dbpath is None:
            dburi = 'sqlite:///:memory:'
        else:
            dburi = 'sqlite:///%s' % dbpath
            
        engine = sql.create_engine(dburi)
        db = sql.MetaData(engine)

        sql.Table('records', db,
                  sql.Column('record_id', sql.Integer, primary_key=True),
                  sql.Column('name', sql.Unicode, unique=True, index=True),
                  sql.Column('when_modified', sql.DateTime, index=True),
                  sql.Column('deleted', sql.Boolean),
                  sql.Column('content_type', sql.Unicode),
                  sql.Column('is_set', sql.Boolean),
                  sql.Column('is_asset', sql.Boolean),
                  sql.Column('sets', sql.Unicode)
                  )
        
        sql.Table('metadata', db,
                  sql.Column('metadata_id', sql.Integer, primary_key=True),
                  sql.Column('record_id', sql.Integer,
                             sql.ForeignKey('records.record_id'), index=True),
                  sql.Column('field', sql.String),
                  sql.Column('value', sql.Unicode),
                  sql.Column('reference', sql.Integer)
                  )

        db.create_all()
        return db

    def _get_set_ids(self):
        for record in self.records.select(
            self.records.c.is_set == True).execute():
            yield record.name
        
    def _get_record_id(self, id):
        result = None
        for record in self.records.select(
            self.records.c.name == id).execute():
            result = record['record_id']
        return result
    
    def get_record(self, id):
        result = None
        for record in self.records.select(
            self.records.c.name == id).execute():

            result = {'id': record['name'],
                      'deleted': record['deleted'],
                      'is_set': record['is_set'],
                      'content_type': record['content_type'],
                      'when_modified': record['when_modified'],
                      }
            break
        
        return result
                
    def get_metadata(self, id):
        result = {}
        for record in self.metadata.select(
            sql.and_(self.records.c.name == id,
                     self.metadata.c.record_id == self.records.c.record_id)).execute():

            result.setdefault(record['field'], []).append(record['value'])

        return result or None

    def get_sets(self, id):
        result = []

        for record in self.records.select(
            self.records.c.name == id).execute():
            result = record['sets'].strip().split(' ')
        
        return result

    def get_assets(self, id):
        assets = self.get_metadata(id)
        if assets is None:
            return []
        assets = assets.get('asset', [])
        result = []
        for asset_id in assets:
            md = self.get_metadata(asset_id)
            data = {}
            data['mimetype'] = md.pop('mimetype')[0]
            data['url'] = md.pop('url')[0]
            data['absolute_uri'] = md.pop('absolute_uri')[0]
            data['filename'] = md.pop('filename')[0]
            data['md5'] = md.pop('md5')[0]
            data['metadata'] = md
            result.append(data)
        
        return result
    
    def get_set(self, id):
        md = self.get_metadata(id)
        if not md:
            return {}
        result = {'name': md['name'][0],
                  'description': md['description'][0],
                  'id': id}
        return result

    def remove_content(self, id):
        rid = self._get_record_id(id)
        for result in self.records.delete(self.records.c.record_id == rid).execute():
            pass
        self._remove_metadata(rid)
        return True

    def flush_update(self):
        self.records.insert().execute(self._record_cache)
        self._record_cache = []
        self.metadata.insert().execute(self._metadata_cache)
        self._metadata_cache = []
        
    def add_content(self, id, sets, record_data, meta_data, assets_data):
        record_id = self._add_record(record_data, sets)
        self._add_metadata(record_id, meta_data)

        for num, asset_data in enumerate(assets_data):
            asset_name = u'%s:asset:%s' % (id, num)
            self._add_asset(record_id, asset_name, asset_data)
        
        return record_id

    def _add_record(self, record_data, sets):
        self._record_id += 1
        record_id = self._record_id
        rowdata = {'record_id': record_id,
                   'name': record_data['id'],
                   'deleted': record_data['deleted'],
                   'is_set': record_data['is_set'],
                   'is_asset': record_data.get('is_asset', False),
                   'sets': u' %s ' % ' '.join(sets),
                   'content_type': record_data['content_type'],
                   'when_modified': record_data['when_modified']}
        
        self._record_cache.append(rowdata)

        for set in sets:
            # add dynamic sets
            if not set in self._set_ids:
                self.add_set(set, set)
        
        return record_id

    def _add_metadata(self, record_id, meta_data):
        for key, vals in meta_data.items():
            for val in vals:
                self._metadata_cache.append({'field': key,
                                             'value': val,
                                             'record_id': record_id})

    def _remove_metadata(self, record_id):
        asset_ids = []
        self.metadata.delete(self.metadata.c.record_id == record_id).execute()

    def _add_asset(self, record_id, asset_name, asset_data):

        # an asset is just a record with is_asset == True
        record_data = {'id': asset_name,
                       'deleted': False,
                       'is_set': False,
                       'is_asset': True,
                       'content_type': u'',
                       'when_modified': datetime.datetime.now()
                       }

        asset_id = self._add_record(record_data, [])

        # assets have required metadata        
        meta_data = {'filename': [asset_data['filename']],
                    'url': [asset_data['url']],
                    'absolute_uri': [asset_data['absolute_uri']],
                    'md5': [asset_data['md5']],
                    'mimetype': [asset_data['mimetype']],
                   }
        
        # additional metada can be provided
        meta_data.update(asset_data['metadata'])
        
        self._add_metadata(asset_id, meta_data)
        # relate the asset record to the publication record
        self._add_metadata(record_id, {u'asset': [asset_name]})

    def add_set(self, set_id, name, description=None):
        
        if description is None:
            description = [u'']
        elif not isinstance(description, list):
            description = [description]

        record_data = {'id': set_id,
                       'content_type': u'set',
                       'deleted': False,
                       'sets': u'',
                       'is_set': True,
                       'is_asset': False,
                       'when_modified': datetime.datetime.now()}
        
        meta_data  =  {'id':[set_id],
                       'name': [name],
                       'description': description}


        if not set_id in self._set_ids:
            # add a new set
            record_id = self.add_content(set_id, [], record_data, meta_data, {})
            self._set_ids.add(set_id)
        else:
            # set is allready there, update the metadata
            record_id = self._get_record_id(set_id)
            self._remove_metadata(record_id)
            self._add_metadata(record_id, meta_data)

        return record_id
                         
    def remove_set(self, id):
        self.remove_content(id)

    def oai_sets(self, offset=0, batch_size=20):
        for row in self.records.select(self.records.c.is_set==True
            ).offset(offset).limit(batch_size).execute():
            result = {}
            for data in self.metadata.select(
                self.metadata.c.record_id==row['record_id']).execute():
                result[data.field] = data.value
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

        if batch_size < 0:
            batch_size = 0

        # make sure until date is set, and not in future
        if until_date == None or until_date > datetime.datetime.now():
            until_date = datetime.datetime.now()


        query = self.records.select(sql.and_(self.records.c.is_set == False,
                                             self.records.c.is_asset == False))

        # filter dates
        query.append_whereclause(self.records.c.when_modified <= until_date)

        if not identifier is None:
            query.append_whereclause(self.records.c.name == identifier)

        if not from_date is None:
            query.append_whereclause(self.records.c.when_modified >= from_date)

        # filter sets

        setclauses = []
        for set_id in sets:
            setclauses.append(
                self.records.c.sets.like(u'%% %s %%' % set_id))
            
        if setclauses:
            query.append_whereclause(sql.or_(*setclauses))
            
        # extra filter sets
        
        filter_setclauses = []
        for set_id in filter_sets:
            filter_setclauses.append(
                self.records.c.sets.like(u'%% %s %%' % set_id))
            
        if filter_setclauses:
            query.append_whereclause(sql.or_(*filter_setclauses))

        # filter not_sets

        not_setclauses = []
        for set_id in not_sets:
            not_setclauses.append(
                self.records.c.sets.like(u'%% %s %%' % set_id))

            
        if not_setclauses:
            query.append_whereclause(sql.not_(
                sql.or_(*not_setclauses)))

        for row in query.distinct().offset(offset).limit(batch_size).execute():
            record = dict(row)
            record['id'] = record['name']
            del record['name']
            record['sets'] = record['sets'].strip().split(' ')
            if record['sets'] == [u'']:
                record['sets'] = []
            yield {'record': record,
                   'sets': record['sets'],
                   'metadata': self.get_metadata(row['name']) or {},
                   'assets':{}}
       
    def empty_database(self):
        self.records.delete().execute()
        self.metadata.delete().execute()

        self._record_id = 0
        self._record_cache = []
        self._metadata_cache = []
        #self._set_ids = set(self._get_set_ids())

