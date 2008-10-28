from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite, main
import logging

from moai.content import ListBasedContentProvider, DatabaseUpdater
from moai.database import BTreeDatabase

DATA = [{'id': u'id:1',
         'content_type': u'publication',
         'when_modified': datetime(2008, 01, 01, 14, 30, 00),
         'deleted': False,
         'scope': u'public',
         'sets': [u'stuff', u'publications', 'top']
         },
        {'id': u'id:2',
         'content_type': u'dataset',
         'when_modified': datetime(2004, 01, 01, 14, 30, 00),
         'deleted': False,
         'scope': u'public',
         'sets': [u'stuff', u'datasets']
         },
        {'id': u'id:3',
         'content_type': u'publication',
         'when_modified': datetime(2006, 01, 01, 14, 30, 00),
         'deleted': False,
         'scope': u'public',
         'sets': [u'stuff', 'publications']
         }
        ]

SETS = [{'id': u'stuff',
         'name': u'Stuff',
         'description': u'Assorted Stuffs'},
        {'id': u'publications',
         'name': u'publication set'},
        {'id': u'datasets',
         'name': u'Datasets'},
        {'id': u'top',
         'name': u'Top publications'}
        ]

class DatabaseTest(TestCase):

    def setUp(self):
        self.db = BTreeDatabase()
        provider = ListBasedContentProvider(DATA, SETS)
        DatabaseUpdater(provider, self.db, logging).update()
        
    def tearDown(self):
        del self.db

    def testSetAddRemove(self):
        # we have 4 sets to begin with
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 4)
        self.db.add_set(id=u'added set',
                        name=u'An added set',
                        description=u'A set description')
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 5)
        self.assertEquals(self.db.get_set(u'added set')['name'], 'An added set')
        self.db.remove_set(u'added set')
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 4)

    def testRecordAddRemove(self):
        # we have 3 records to begin with
        result = list(self.db.oai_query(offset=0, batch_size=100))
        self.assertEquals(len(result), 3)
        self.db.remove_content('id:1')
        result = list(self.db.oai_query(offset=0, batch_size=100))
        self.assertEquals(len(result), 2)

        
    def testOAISets(self):
        result = list(self.db.oai_sets(offset=0, batch_size=100))
        self.assertEquals(len(result), 4)
        result = list(self.db.oai_sets(offset=2, batch_size=100))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_sets(offset=3, batch_size=100))
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
        result = list(self.db.oai_query(sets=['stuff']))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(sets=['publications']))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(sets=['datasets']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(sets=['datasets', 'publications']))
        self.assertEquals(len(result), 3)
        result = list(self.db.oai_query(not_sets=['stuff']))
        self.assertEquals(len(result), 0)
        result = list(self.db.oai_query(not_sets=['publications']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(not_sets=['datasets']))
        self.assertEquals(len(result), 2)
        result = list(self.db.oai_query(sets=['stuff'], not_sets=['publications']))
        self.assertEquals(len(result), 1)
        result = list(self.db.oai_query(sets=['publications'], filter_sets=['top']))
        self.assertEquals(len(result), 1)

   
def test_suite():
    return TestSuite((makeSuite(DatabaseTest), ))


if __name__ == '__main__':
    main(defaultTest='test_suite')
