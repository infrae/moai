from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite, main
import logging

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.database.sqlite import SQLiteDatabase
from moai.error import UnknownRecordID

from sqlalchemy.exc import IntegrityError

class BtreeDatabaseTest(TestCase):

    def setUp(self):
        self.db = BTreeDatabase()
        provider = ListBasedContentProvider(DATA)
        updater = DatabaseUpdater(provider, DictBasedContentObject, 
                                  self.db, logging)
        updater.update_provider()
        updater.update_database()
        
    def tearDown(self):
        del self.db

    def testGetRecord(self):
        self.assertEquals(self.db.get_record(u'bla'), None)
        record = self.db.get_record(u'id:1')
        self.assertEquals(type(record.get('id')), unicode)
        self.assertEquals(type(record.get('when_modified')), datetime)
        self.assertEquals(type(record.get('deleted')), bool)
        self.assertEquals(type(record.get('is_set')), bool)
        self.assertEquals(type(record.get('content_type')), unicode)

    def testGetMetadata(self):
        self.assertEquals(self.db.get_metadata(u'bla'), None)
        record = self.db.get_metadata(u'id:1')
        self.assertEquals(record.get('abstract'),
                          [u'A test publication'])

    def testGetSets(self):
        self.assertEquals(self.db.get_sets(u'bla'), [])
        sets = self.db.get_sets(u'id:1')
        self.assertEquals(len(sets), 3)

    def testGetAssets(self):
        self.assertEquals(self.db.get_assets(u'bla'), [])
        self.assertEquals(self.db.get_assets(u'id:1'), [])
        assets = self.db.get_assets(u'id:2')
        self.assertEquals(len(assets), 1)
        asset = assets[0]
        self.assertEquals(type(asset.get('filename')), unicode)
        self.assertEquals(type(asset.get('url')), unicode)
        self.assertEquals(type(asset.get('mimetype')), unicode)
        self.assertEquals(type(asset.get('md5')), unicode)
        self.assertEquals(type(asset.get('absolute_uri')), unicode)
        self.assertEquals(type(asset.get('metadata')), dict)
        self.assertTrue(asset['metadata'].has_key('type'))
        self.assertEquals(asset['metadata']['type'], [u'preprint'])

    def testSetAddRemove(self):
        # we have 5 sets to begin with
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 5)
        self.db.add_set(u'added set', u'An added set', description=u'A set description')
        self.db.flush_update()
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 6)
        self.assertEquals(self.db.get_set(u'added set')['name'], 'An added set')
        self.db.remove_set(u'added set')
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 5)

    def testRecordAddRemove(self):
        # we have 3 records to begin with
        result = list(self.db.oai_query(offset=0, batch_size=100))
        self.assertEquals(len(result), 3)
        self.db.remove_content(u'id:1')
        result = list(self.db.oai_query(offset=0, batch_size=100))
        self.assertEquals(len(result), 2)
        
    def testOAISets(self):
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 5)
        result = list(self.db.oai_sets(offset=2, batch_size=100))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_sets(offset=4, batch_size=100))
        self.assertEquals(len(result), 1)

    def testOAIQueryBatching(self):
        result = list(self.db.oai_query(offset=0, batch_size=100))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(offset=1, batch_size=100))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(offset=2, batch_size=100))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(offset=3, batch_size=100))
        self.assertEquals(result, [])
        result = list(self.db.oai_query(offset=10, batch_size=100))
        self.assertEquals(result, [])
        result = list(self.db.oai_query(batch_size=2))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(offset=0, batch_size=0))
        self.assertEquals(result, [])
        result = list(self.db.oai_query(batch_size=-1))
        self.assertEquals(result, [])

    def testOAIQueryDateStamps(self):
        result = list(self.db.oai_query())
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(from_date=datetime(2000, 01, 01)))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(from_date=datetime(2005, 01, 01)))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(from_date=datetime(2007, 01, 01)))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(from_date=datetime(2020, 01, 01)))
        self.assertEquals(len(result), 0)
        result = list(self.db.oai_query(until_date=datetime(2000, 01, 01)))
        self.assertEquals(len(result), 0)
        result = list(self.db.oai_query(until_date=datetime(2005, 01, 01)))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(until_date=datetime(2007, 01, 01)))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(until_date=datetime(2020, 01, 01)))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(from_date=datetime(2003, 01, 01),
                                        until_date=datetime(2005, 01, 01)))
        self.assertEquals(len(result), 1)

    def testOAIQuerySets(self):
        result = list(self.db.oai_query(sets=[u'stuff']))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(sets=[u'publications']))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(sets=[u'datasets']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(sets=[u'datasets',
                                              u'publications']))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(not_sets=[u'stuff']))
        self.assertEquals(len(result), 0)
        result = list(self.db.oai_query(not_sets=[u'publications']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(not_sets=[u'datasets']))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(sets=[u'stuff'], 
                                        not_sets=['publications']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(sets=[u'publications'], 
                                        filter_sets=['top']))
        self.assertEquals(len(result), 1)

    def testEmptyDatabase(self):
        result = list(self.db.oai_sets()) 
        self.assertEquals(len(result), 5)
        result = list(self.db.oai_query())
        self.assertEquals(len(result), 3)

        self.db.empty_database()

        result = list(self.db.oai_sets()) 
        self.assertEquals(result, [])
        result = list(self.db.oai_query())
        self.assertEquals(result, [None])


class SQLiteDatabaseTest(BtreeDatabaseTest):
    def setUp(self):
        self.db = SQLiteDatabase()
        provider = ListBasedContentProvider(DATA)
        updater = DatabaseUpdater(provider, DictBasedContentObject, 
                                  self.db, logging)
        updater.update_provider()
        updater.update_database()

    def tearDown(self):
        del self.db

    def testEmptyDatabase(self):
        result = list(self.db.oai_sets())
        self.assertEquals(len(result), 5)
        result = list(self.db.oai_query())
        self.assertEquals(len(result), 3) 

        self.db.empty_database()
              
        result = list(self.db.oai_sets())
        self.assertEquals(result, [])
        result = list(self.db.oai_query())
        self.assertEquals(result, [])
        
        
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(BtreeDatabaseTest))
    suite.addTest(makeSuite(SQLiteDatabaseTest))
    return suite


if __name__ == '__main__':
    main(defaultTest='test_suite')


DATA = [{'id': u'id:1',
         'label': u'Publication 1',
         'content_type': u'publication',
         'when_modified': datetime(2008, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [u'stuff', u'publications', u'top'],
         'is_set': False,
         'abstract': [u'A test publication']
         },
        {'id': u'id:2',
         'label': u'Dataset 1',
         'content_type': u'dataset',
         'when_modified': datetime(2004, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [u'stuff', u'datasets', u'dynamic'],
         'is_set': False,
         'assets': [{
             u'filename': u'test.txt',
             u'url': u'http://example.org/assets/test.txt',
             u'mimetype': u'text/plain',
             u'md5': u'730652c70a12db042b8842f5049390d4',
             u'absolute_uri': u'file:///tmp/test.txt',
             u'metadata': {u'access': [u'public'],
                           u'type': [u'preprint']}}]

         },
        {'id': u'id:3',
         'label': u'Publication 2',
         'content_type': u'publication',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [u'stuff', u'publications'],
         'is_set': False,
         },
        {'id': u'stuff',
         'label': u'Stuff',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         },
        {'id': u'publications',
         'label': u'publication set',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         'abstract': [u'A test publication']
         },
        {'id': u'datasets',
         'label': u'datasets',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         },
        {'id': u'top',
         'label': u'top publications',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         },
        ]


