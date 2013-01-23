import datetime
import json
from pkg_resources import iter_entry_points

import sqlalchemy as sql

from moai.utils import check_type

def get_database(uri, config=None):
    prefix = uri.split(':')[0]
    for entry_point in iter_entry_points(group='moai.database', name=prefix):
        dbclass = entry_point.load()
        try:
            return dbclass(uri, config)
        except TypeError:
            # ugly backwards compatibility hack
            return dbclass(uri)
    raise ValueError('No such database registered: %s' % prefix)


class SQLDatabase(object):
    """Sql implementation of a database backend
    This implements the :ref:`IDatabase` interface, look there for
    more documentation.
    """

    def __init__(self, dburi=None):
        self._uri = dburi
        self._db = self._connect()
        self._records = self._db.tables['records']
        self._sets = self._db.tables['sets']
        self._setrefs = self._db.tables['setrefs']
        self._reset_cache()
        
    def _connect(self):
        dburi = self._uri
        if dburi is None:
            dburi = 'sqlite:///:memory:'
            
        engine = sql.create_engine(dburi)
        db = sql.MetaData(engine)
        
        sql.Table('records', db,
                  sql.Column('record_id', sql.Unicode, primary_key=True),
                  sql.Column('modified', sql.DateTime, index=True),
                  sql.Column('deleted', sql.Boolean),
                  sql.Column('metadata', sql.String))
        
        sql.Table('sets', db,
                  sql.Column('set_id', sql.Unicode, primary_key=True),
                  sql.Column('hidden', sql.Boolean),
                  sql.Column('name', sql.Unicode),
                  sql.Column('description', sql.Unicode))

        sql.Table('setrefs', db,
                  sql.Column('record_id', sql.Integer, 
                             sql.ForeignKey('records.record_id'),
                             index=True, primary_key=True),
                  sql.Column('set_id', sql.Integer,
                             sql.ForeignKey('sets.set_id'),
                             index=True, primary_key=True))
        
        db.create_all()
        return db

    def flush(self):
        oai_ids = set()
        for row in sql.select([self._records.c.record_id]).execute():
            oai_ids.add(row[0])
        for row in sql.select([self._sets.c.set_id]).execute():
            oai_ids.add(row[0])

        deleted_records = []
        deleted_sets = []
        deleted_setrefs = []

        inserted_records = []
        inserted_sets = []
        inserted_setrefs = []

        
        for oai_id, item in self._cache['records'].items():
            if oai_id in oai_ids:
                # record allready exists
                deleted_records.append(oai_id)
            item['record_id'] = oai_id
            inserted_records.append(item)

        for oai_id, item in self._cache['sets'].items():
            if oai_id in oai_ids:
                # set allready exists
                deleted_sets.append(oai_id)
            item['set_id'] = oai_id
            inserted_sets.append(item)

        for record_id, set_ids in self._cache['setrefs'].items():
            deleted_setrefs.append(record_id)
            for set_id in set_ids:
                inserted_setrefs.append(
                    {'record_id':record_id, 'set_id': set_id})

        # delete all processed records before inserting
        if deleted_records:
            self._records.delete(
                self._records.c.record_id == sql.bindparam('record_id')
                ).execute(
                [{'record_id': rid} for rid in deleted_records])
        if deleted_sets:
            self._sets.delete(
                self._sets.c.set_id == sql.bindparam('set_id')
                ).execute(
                [{'set_id': sid} for sid in deleted_sets])
        if deleted_setrefs:
            self._setrefs.delete(
                self._setrefs.c.record_id == sql.bindparam('record_id')
                ).execute(
                [{'record_id': rid} for rid in deleted_setrefs])

        # batch inserts
        if inserted_records:
            self._records.insert().execute(inserted_records)
        if inserted_sets:
            self._sets.insert().execute(inserted_sets)
        if inserted_setrefs:
            self._setrefs.insert().execute(inserted_setrefs)

        self._reset_cache()

    def _reset_cache(self):
        self._cache = {'records': {}, 'sets': {}, 'setrefs': {}}
        
            
    def update_record(self, oai_id, modified, deleted, sets, metadata):
        # adds a record, call flush to actually store in db

        check_type(oai_id,
                   unicode,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "oai_id"')
        check_type(modified,
                   datetime.datetime,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "modified"')
        check_type(deleted,
                   bool,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "deleted"')
        check_type(sets,
                   dict,
                   unicode_values=True,
                   recursive=True,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "sets"')
        check_type(metadata,
                   dict,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "metadata"')

        def date_handler(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            else:
                raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

        metadata = json.dumps(metadata, default=date_handler)
        self._cache['records'][oai_id] = (dict(modified=modified,
                                               deleted=deleted,
                                               metadata=metadata))
        self._cache['setrefs'][oai_id] = []
        for set_id in sets:
            self._cache['sets'][set_id] = dict(
                name = sets[set_id]['name'],
                description = sets[set_id].get('description'),
                hidden = sets[set_id].get('hidden', False))
            self._cache['setrefs'][oai_id].append(set_id)
            
    def get_record(self, oai_id):
        row = self._records.select(
            self._records.c.record_id == oai_id).execute().fetchone()
        if row is None:
            return
        record = {'id': row.record_id,
                  'deleted': row.deleted,
                  'modified': row.modified,
                  'metadata': json.loads(row.metadata),
                  'sets': self.get_setrefs(oai_id)}
        return record

    def get_set(self, oai_id):
        row = self._sets.select(
            self._sets.c.set_id == oai_id).execute().fetchone()
        if row is None:
            return
        return {'id': row.set_id,
                'name': row.name,
                'description': row.description,
                'hidden': row.hidden}

    def get_setrefs(self, oai_id, include_hidden_sets=False):
        set_ids = []
        query = sql.select([self._setrefs.c.set_id])
        query.append_whereclause(self._setrefs.c.record_id == oai_id)
        if include_hidden_sets == False:
            query.append_whereclause(
                sql.and_(self._sets.c.set_id == self._setrefs.c.set_id,
                         self._sets.c.hidden == include_hidden_sets))
        
        for row in query.execute():
            set_ids.append(row[0])
        set_ids.sort()
        return set_ids

    def record_count(self):
        return sql.select([sql.func.count('*')],
                          from_obj=[self._records]).execute().fetchone()[0]

    def set_count(self):
        return sql.select([sql.func.count('*')],
                          from_obj=[self._sets]).execute().fetchone()[0]
        
    def remove_record(self, oai_id):
        self._records.delete(
            self._records.c.record_id == oai_id).execute()
        self._setrefs.delete(
            self._setrefs.c.record_id == oai_id).execute()

    def remove_set(self, oai_id):
        self._sets.delete(
            self._sets.c.set_id == oai_id).execute()
        self._setrefs.delete(
            self._setrefs.c.set_id == oai_id).execute()

    def oai_sets(self, offset=0, batch_size=20):
        for row in self._sets.select(
              self._sets.c.hidden == False
            ).offset(offset).limit(batch_size).execute():
            yield {'id': row.set_id,
                   'name': row.name,
                   'description': row.description}

    def oai_earliest_datestamp(self):
        row = sql.select([self._records.c.modified],
                         order_by=[sql.asc(self._records.c.modified)]
                         ).limit(1).execute().fetchone()
        if row:
            return row[0]
        return datetime.datetime(1970, 1, 1)
    
    def oai_query(self,
                  offset=0,
                  batch_size=20,
                  needed_sets=None,
                  disallowed_sets=None,
                  allowed_sets=None,
                  from_date=None,
                  until_date=None,
                  identifier=None):

        needed_sets = needed_sets or []
        disallowed_sets = disallowed_sets or []
        allowed_sets = allowed_sets or []
        if batch_size < 0:
            batch_size = 0

        # make sure until date is set, and not in future
        if until_date == None or until_date > datetime.datetime.utcnow():
            until_date = datetime.datetime.utcnow()


        query = self._records.select(
            order_by=[sql.desc(self._records.c.modified)])

        # filter dates
        query.append_whereclause(self._records.c.modified <= until_date)

        if not identifier is None:
            query.append_whereclause(self._records.c.record_id == identifier)

        if not from_date is None:
            query.append_whereclause(self._records.c.modified >= from_date)

        # filter sets

        setclauses = []
        for set_id in needed_sets:
            alias = self._setrefs.alias()
            setclauses.append(
                sql.and_(
                alias.c.set_id == set_id,
                alias.c.record_id == self._records.c.record_id))
            
        if setclauses:
            query.append_whereclause((sql.and_(*setclauses)))
            
        allowed_setclauses = []
        for set_id in allowed_sets:
            alias = self._setrefs.alias()
            allowed_setclauses.append(
                sql.and_(
                alias.c.set_id == set_id,
                alias.c.record_id == self._records.c.record_id))
            
        if allowed_setclauses:
            query.append_whereclause(sql.or_(*allowed_setclauses))

        disallowed_setclauses = []
        for set_id in disallowed_sets:
            alias = self._setrefs.alias()
            disallowed_setclauses.append(
                sql.exists([self._records.c.record_id],
                           sql.and_(
                alias.c.set_id == set_id,
                alias.c.record_id == self._records.c.record_id)))
            
        if disallowed_setclauses:
            query.append_whereclause(sql.not_(sql.or_(*disallowed_setclauses)))
            
        for row in query.distinct().offset(offset).limit(batch_size).execute():
            yield {'id': row.record_id,
                   'deleted': row.deleted,
                   'modified': row.modified,
                   'metadata': json.loads(row.metadata),
                   'sets': self.get_setrefs(row.record_id)
                   }

