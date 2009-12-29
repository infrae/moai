from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite, main
import logging
import os

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.sqlite import SQLiteDatabase
from moai.database.btree import BTreeDatabase
from sqlalchemy.exc import IntegrityError

class UpdaterTest(TestCase):

    def setUp(self):
        self.db = SQLiteDatabase()
        self.provider = ListBasedContentProvider(DATA)
        self.updater = DatabaseUpdater(self.provider, DictBasedContentObject, 
                                       self.db, logging)

    def tearDown(self):
        del self.db

    def test_update_provider(self):
        # Check updating provider
        result = self.updater.update_provider()
        expRes = [0, 1, 2, 3, 4, 5, 6]
        self.assertEquals(result, expRes)

        # Check updating database 
        result = self.updater.update_database_iterate()
        update_list1 = []
        for line in result:
            update_list1.append(line)

        # Modify DATA for tests below, remember changes 
        store_data = (DATA[5]['when_modified'], DATA[6]['when_modified'])
        DATA[5]['when_modified'] = ''
        DATA[6].pop('when_modified')

        # Check updating provider with modified DATA and from_date 
        from_date = datetime(2006, 01, 01) 
        result = self.updater.update_provider(from_date)
        expRes = [0, 2, 3, 4]
        self.assertEquals(result, expRes)

        # Check updating the database with modified DATA
        result = self.updater.update_database_iterate()
        update_list2 = []
        try:
            for line in result:
                update_list2.append(line)
        except AssertionError:
            pass
        self.assertEquals(update_list1[:-2], update_list2)

        # Restore DATA for other tests
        DATA[5]['when_modified'] = store_data[0] 
        DATA[6]['when_modified'] = store_data[1]


    def test_update_database(self):
        # The first database-update succeeds
        self.updater.update_provider()
        self.updater.update_database()
        
        # The second fails on non-unique ids 
        self.assertRaises(IntegrityError, self.updater.update_database)

        # No errors if the db is emptied
        self.db.empty_database()
        self.updater.update_database()

        # Check if a flush_threshold of 1 fails
        self.db.empty_database()
        self.updater.flush_threshold = 1 
        self.updater.update_database()
        self.updater.flush_threshold = -1

        # Check the supress_error variable
        self.updater.update_database(supress_errors=True)

      
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(UpdaterTest))
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
         },
        {'id': u'datasets',
         'label': u'datasets',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 31, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         },
        {'id': u'top',
         'label': u'top publications',
         'content_type': u'collection',
         'when_modified': datetime(2006, 01, 01, 14, 32, 00),
         'deleted': False,
         'sets': [],
         'is_set': True,
         },
        ]
