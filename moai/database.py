import datetime
import json

import sqlalchemy as sql

from moai.utils import check_type

class Database(object):
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
                  sql.Column('data', sql.String))
        
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
            self._records.delete().execute(
                [{'record_id': rid} for rid in deleted_records])
        if deleted_sets:
            self._sets.delete().execute(
                [{'set_id': sid} for sid in deleted_sets])
        if deleted_setrefs:
            self._setrefs.delete().execute(
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
        
            
    def update_record(self, oai_id, modified, deleted, sets, data):
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
                   unicode_keys=True,
                   unicode_values=True,
                   recursive=True,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "sets"')
        check_type(data,
                   dict,
                   prefix="record %s" % oai_id,
                   suffix='for parameter "dict"')
        
        data['sets'] = sets
        data = json.dumps(data)
        self._cache['records'][oai_id] = (dict(modified=modified,
                                               deleted=deleted,
                                               data=data))
        self._cache['setrefs'][oai_id] = []
        for set_id in sets:
            self._cache['sets'][set_id] = dict(
                name = sets[set_id]['name'],
                description = sets[set_id].get('description'),
                hidden = sets[set_id].get('hidden', False))
            self._cache['setrefs'][oai_id].append(set_id)
            
    def get_record(self, oai_id):
        row = self.records.select(
            self._records.c.record_id == oai_id).execute().fetch_one()
        if row is None:
            return {}
        return dict(row)

    def get_set(self, oai_id):
        row = self.records.select(
            self._sets.c.set_id == oai_id).execute().fetch_one()
        if row is None:
            return {}
        return dict(row)

    def remove_record(self, oai_id):
        for result in self._records.delete(
            self._records.c.record_id == oai_id).execute():
            pass
        for result in self._setrefs.delete(
            self._setrefs.c.record_id == oai_id).execute():
            pass

    def remove_set(self, oai_id):
        for result in self._sets.delete(
            self._sets.c.set_id == oai_id).execute():
            pass
        for result in self._setrefs.delete(
            self._setrefs.c.set_id == oai_id).execute():
            pass

    def oai_sets(self, offset=0, batch_size=20):
        for row in self._sets.select(
              self._sets.c.hidden == False
            ).offset(offset).limit(batch_size).execute():
            yield {'id': row.set_id,
                   'name': row.name,
                   'description': row.description}
            
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
        for set_id in sets:
            setclauses.append(
                sql.and_(
                self._setrefs.c.set_id == set_id,
                self._setrefs.c.record_id == self._records.c.record_id))
            
        if setclauses:
            query.append_whereclause(sql.or_(*setclauses))
            
        # extra filter sets
        
        filter_setclauses = []
        for set_id in filter_sets:
            filter_setclauses.append(
                sql.and_(
                self._setrefs.c.set_id == set_id,
                self._setrefs.c.record_id == self._records.c.record_id))
            
        if filter_setclauses:
            query.append_whereclause(sql.or_(*filter_setclauses))

        # filter not_sets

        not_setclauses = []
        for set_id in not_sets:
            not_setclauses.append(
                sql.and_(
                self._setrefs.c.set_id == set_id,
                self._setrefs.c.record_id == self._records.c.record_id))
            
        if not_setclauses:
            query.append_whereclause(sql.not_(sql.or_(*not_setclauses)))

        for row in query.distinct().offset(offset).limit(batch_size).execute():
            record = {'id': row.record_id,
                      'deleted': row.deleted,
                      'modified': row.modified,
                      'data': json.loads(row.data)}
            yield {'record': record,
                   'sets': record['data']['sets'],
                   'metadata': record['data'],
                   'assets':{}}
       
    def empty_database(self):
        self._records.delete().execute()
        self._sets.delete().execute()
        self._setrefs.delete().execute()

