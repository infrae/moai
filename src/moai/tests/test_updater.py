import logging
import os
import tempfile
import StringIO
import copy
from datetime import datetime
from unittest import TestCase, TestSuite, makeSuite, main

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.sqlite import SQLiteDatabase
from moai.database.btree import BTreeDatabase
from sqlalchemy.exc import IntegrityError
from moai.tests.test_database import DATA
from moai.server import Server, FeedConfig
from moai.http.cgi import CGIRequest
from moai.core import MOAI


class UpdaterTest(TestCase):

    def setUp(self):
        self.test_data = copy.deepcopy(DATA)
        self.db = SQLiteDatabase()
        self.provider = ListBasedContentProvider(self.test_data)
        self.updater = DatabaseUpdater(self.provider, DictBasedContentObject, 
                                       self.db, logging)
        self.updater.flush_threshold = -1

    def tearDown(self):
        del self.db

    def request(self, url, **kwargs):
        req = CGIRequest('http://localhost/repo/test' + url, **kwargs)
        req.stream = StringIO.StringIO()
        self.server.handle_request(req)
        req.stream.seek(0)
        return req.stream.read()

    def setup_server(self):
        # init moai, so metadata formats get registered
        m = MOAI(logging, debug=True)
        
        config = FeedConfig('test', 'A test Repository',
                            'http://localhost/repo/test',
                            logging)
        self.server = Server('http://localhost/repo', self.db)
        self.server.add_config(config)

    def setup_test_provider(self, data, supress_errors=True):
        if 'server' not in dir(self):
            self.setup_server()

        self.db.empty_database()

        provider = ListBasedContentProvider(data)
        self.updater = DatabaseUpdater(provider, DictBasedContentObject, self.db, logging)
        self.updater.update_provider()
        if supress_errors:
            self.updater.update_database(supress_errors=True)
        else:
            self.assertRaises(Exception, self.updater.update_database)

    def test_update_provider(self):
        # Check updating provider
        result = self.updater.update_provider()
        expRes = [0, 1, 2, 3, 4, 5, 6]
        self.assertEqual(result, expRes)

        # Check updating database 
        result = self.updater.update_database_iterate()
        update_list1 = []
        for line in result:
            update_list1.append(line)

        # Modify data for tests below
        self.test_data[5]['when_modified'] = ''
        self.test_data[6].pop('when_modified')

        # Check updating provider with modified data and from_date 
        from_date = datetime(2006, 01, 01) 
        result = self.updater.update_provider(from_date)
        expRes = [0, 2, 3, 4]
        self.assertEqual(result, expRes)

        # Update the database with failing data, fails last 2 records
        result = self.updater.update_database_iterate()
        update_list2 = []
        try:
            for line in result:
                update_list2.append(line)
        except AssertionError:
            pass
        self.assertEqual(update_list1[:-2], update_list2)

        # The same, but continue on errors
        result = self.updater.update_database_iterate(supress_errors=True)
        update_list2 = []
        for line in result:
            update_list2.append(line)
        self.assertEqual(update_list1[:-2], update_list2[:-2])
        self.assertNotEqual(update_list1[-2:], update_list2[-2:])

    def test_update_database(self):
        self.updater.update_provider()

        # Normal update works, but fails on non-uique ids
        self.updater.update_database()
        self.assertRaises(IntegrityError, self.updater.update_database)
        # But suppress errors works, and emptying the db works
        self.updater.update_database(supress_errors=True)
        self.db.empty_database()
        self.updater.update_database()

        # Same tests with threshold = 1
        self.updater.flush_threshold = 1
        self.db.empty_database()

        # Normal update works, but fails on non-uique ids
        self.updater.update_database()
        self.assertRaises(IntegrityError, self.updater.update_database)
        # But suppress errors works, and emptying the db works
        self.updater.update_database(supress_errors=True)
        self.db.empty_database()
        self.updater.update_database()

    def test_xml_compatibility(self):
        # These fail when the content is sanatized in the IContentObject implementation

        # Failure in metadata
        test_data = copy.deepcopy(DATA)
        test_data[0]['abstract'] = [u'A test publi\u000bcation']
        self.setup_test_provider(test_data)
        
        response = self.request('', verb='ListRecords', metadataPrefix='oai_dc')
        self.assertFalse('<identifier>oai:id:1</identifier>' in response)
        self.assertTrue('<identifier>oai:id:2</identifier>' in response)
        self.assertTrue('<identifier>oai:id:3</identifier>' in response)

        # Failure in record
        test_data = copy.deepcopy(DATA)
        test_data[1]['id'] = u"i\u000bd:2" 
        self.setup_test_provider(test_data)
        
        response = self.request('', verb='ListRecords', metadataPrefix='oai_dc')
        self.assertTrue('<identifier>oai:id:1</identifier>' in response)
        self.assertFalse('<identifier>oai:id:2</identifier>' in response)
        self.assertFalse(u'<identifier>oai:i\u000bd:2</identifier>' in response)
        self.assertTrue('<identifier>oai:id:3</identifier>' in response)

        # Failure in sets
        test_data = copy.deepcopy(DATA)
        test_data[2]['sets'][0] = u"st\u000buff"
        self.setup_test_provider(test_data)

        response = self.request('', verb='ListRecords', metadataPrefix='oai_dc')
        self.assertTrue('<identifier>oai:id:1</identifier>' in response)
        self.assertTrue('<identifier>oai:id:2</identifier>' in response)
        self.assertFalse('<identifier>oai:id:3</identifier>' in response)

        # Check the supress_errors on _xml_comp_error()
        test_data = copy.deepcopy(DATA)
        test_data[0]['abstract'] = [u'A test publi\u000bcation'] 
        self.setup_test_provider(test_data, False)


def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(UpdaterTest))
    return suite


if __name__ == '__main__':
    main(defaultTest='test_suite')


