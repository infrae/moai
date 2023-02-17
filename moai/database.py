import datetime
import json

import sqlalchemy as sql
from pkg_resources import iter_entry_points

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
            #dburi = 'sqlite:///test.db'

        engine = sql.create_engine(dburi)
        self._conn = engine.connect()
        db = sql.MetaData()

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

        db.create_all(bind=self._conn)
        return db

    def flush(self):
        oai_ids = set()
        for row in self._conn.execute(sql.select(self._records.c.record_id)):
            oai_ids.add(row[0])
        for row in self._conn.execute(sql.select(self._sets.c.set_id)):
            oai_ids.add(row[0])

        deleted_records = []
        deleted_sets = []
        deleted_setrefs = []

        inserted_records = []
        inserted_sets = []
        inserted_setrefs = []

        for oai_id, item in list(self._cache['records'].items()):
            if oai_id in oai_ids:
                # record allready exists
                deleted_records.append(oai_id)
            item['record_id'] = oai_id
            inserted_records.append(item)

        for oai_id, item in list(self._cache['sets'].items()):
            if oai_id in oai_ids:
                # set allready exists
                deleted_sets.append(oai_id)
            item['set_id'] = oai_id
            inserted_sets.append(item)

        for record_id, set_ids in list(self._cache['setrefs'].items()):
            deleted_setrefs.append(record_id)
            for set_id in set_ids:
                inserted_setrefs.append(
                    {'record_id': record_id, 'set_id': set_id})

        # delete all processed records before inserting
        if deleted_records:
            query = sql.delete(self._records).where(
                self._records.c.record_id == sql.bindparam('record_id'))
            self._conn.execute(query,
                [{'record_id': rid} for rid in deleted_records])
        if deleted_sets:
            query = sql.delete(self._sets).where(
                self._sets.c.set_id == sql.bindparam('set_id'))
            self._conn.execute(query,
                [{'set_id': sid} for sid in deleted_sets])
        if deleted_setrefs:
            query = sql.delete(self._setrefs).where(
                self._setrefs.c.record_id == sql.bindparam('record_id'))
            self._conn.execute(query,
                [{'record_id': rid} for rid in deleted_setrefs])

        # batch inserts
        if inserted_records:
            query = self._records.insert()
            self._conn.execute(query, inserted_records)
        if inserted_sets:
            query = self._sets.insert()
            self._conn.execute(query, inserted_sets)
        if inserted_setrefs:
            query = self._setrefs.insert()
            self._conn.execute(query, inserted_setrefs)

        self._reset_cache()

    def _reset_cache(self):
        self._cache = {'records': {}, 'sets': {}, 'setrefs': {}}

    def update_record(self, oai_id, modified, deleted, sets, metadata):
        # adds a record, call flush to actually store in db

        check_type(oai_id,
                   str,
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
                raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))

        metadata = json.dumps(metadata, default=date_handler)
        self._cache['records'][oai_id] = (dict(modified=modified,
                                               deleted=deleted,
                                               metadata=metadata))
        self._cache['setrefs'][oai_id] = []
        for set_id in sets:
            self._cache['sets'][set_id] = dict(
                name=sets[set_id]['name'],
                description=sets[set_id].get('description'),
                hidden=sets[set_id].get('hidden', False))
            self._cache['setrefs'][oai_id].append(set_id)

    def get_record(self, oai_id):
        query = sql.select(self._records).where(
            self._records.c.record_id == oai_id)
        row = self._conn.execute(query).fetchone()
        if row is None:
            return
        record = {'id': row.record_id,
                  'deleted': row.deleted,
                  'modified': row.modified,
                  'metadata': json.loads(row.metadata),
                  'sets': self.get_setrefs(oai_id)}
        return record

    def get_set(self, oai_id):
        query = sql.select(self._sets).where(
            self._sets.c.set_id == oai_id)
        row = self._conn.execute(query).fetchone()
        if row is None:
            return
        return {'id': row.set_id,
                'name': row.name,
                'description': row.description,
                'hidden': row.hidden}

    def get_setrefs(self, oai_id, include_hidden_sets=False):
        set_ids = []
        query = sql.select(self._setrefs.c.set_id).where(
                           self._setrefs.c.record_id == oai_id)
        if not include_hidden_sets:
            query = query.where(
                sql.and_(self._sets.c.set_id == self._setrefs.c.set_id,
                         self._sets.c.hidden == include_hidden_sets))

        for row in self._conn.execute(query):
            set_ids.append(row[0])
        set_ids.sort()
        return set_ids

    def record_count(self):
        query = sql.select(sql.func.count("*")).select_from(self._records)
        return self._conn.execute(query).fetchone()[0]

    def set_count(self):
        query = sql.select(sql.func.count("*")).select_from(self._sets)
        return self._conn.execute(query).fetchone()[0]

    def remove_record(self, oai_id):
        record_query = sql.delete(self._records).where(self._records.c.record_id == oai_id)
        self._conn.execute(record_query)
        setref_query = sql.delete(self._setrefs).where(self._setrefs.c.record_id == oai_id)
        self._conn.execute(setref_query)

    def remove_set(self, oai_id):
        set_query = sql.delete(self._sets).where(self._sets.c.set_id == oai_id)
        self._conn.execute(set_query)
        setref_query = sql.delete(self._setrefs).where(self._setrefs.c.set_id == oai_id)
        self._conn.execute(setref_query)

    def oai_sets(self, offset=0, batch_size=20):
        query = sql.select(self._sets).where(sql.not_(self._sets.c.hidden)).offset(offset).limit(batch_size)
        for row in self._conn.execute(query):
            yield {'id': row.set_id,
                   'name': row.name,
                   'description': row.description}

    def oai_earliest_datestamp(self):
        query = sql.select(self._records.c.modified).order_by(
                           sql.asc(self._records.c.modified)).limit(1)
        row = self._conn.execute(query).fetchone()
        return row[0] if row else datetime.datetime(1970, 1, 1)

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
        if until_date is None or until_date > datetime.datetime.utcnow():
            until_date = datetime.datetime.utcnow()

        query = sql.select(self._records).order_by(
                sql.desc(self._records.c.modified)).where(
                self._records.c.modified <= until_date)

        if identifier is not None:
            query = query.where(self._records.c.record_id == identifier)

        if from_date is not None:
            query = query.where(self._records.c.modified >= from_date)

        # filter sets
        setclauses = []
        for set_id in needed_sets:
            alias = self._setrefs.alias()
            setclauses.append(
                sql.and_(
                    alias.c.set_id == set_id,
                    alias.c.record_id == self._records.c.record_id))

        if setclauses:
            query = query.where((sql.and_(*setclauses)))

        allowed_setclauses = []
        for set_id in allowed_sets:
            alias = self._setrefs.alias()
            allowed_setclauses.append(
                sql.and_(
                    alias.c.set_id == set_id,
                    alias.c.record_id == self._records.c.record_id))

        if allowed_setclauses:
            query = query.where(sql.or_(*allowed_setclauses))

        disallowed_setclauses = []
        for set_id in disallowed_sets:
            alias = self._setrefs.alias()
            query = sql.select(self._records.c.record_id).where(
                    alias.c.set_id == set_id,
                    alias.c.record_id == self._records.c.record_id)
            disallowed_setclauses.append(sql.exists(query))

        if disallowed_setclauses:
            query = query.where(sql.not_(sql.or_(*disallowed_setclauses)))

        for row in self._conn.execute(query.distinct().offset(offset).limit(batch_size)):
            yield {'id': row.record_id,
                   'deleted': row.deleted,
                   'modified': row.modified,
                   'metadata': json.loads(row.metadata),
                   'sets': self.get_setrefs(row.record_id)
                   }
