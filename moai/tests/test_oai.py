from unittest import TestCase, TestSuite, makeSuite, main
import logging
import StringIO

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.database.sqlite import SQLiteDatabase
from moai.server import Server, FeedConfig
from moai.http.cgi import CGIRequest
from moai.tests.test_database import DATA
from moai.core import MOAI

class OAIBtreeTest(TestCase):

    def get_database(self):
        return BTreeDatabase()

    def setUp(self):
        # init moai, so metadata formats get registered
        m = MOAI(logging, debug=True)
        self.db = self.get_database()
        provider = ListBasedContentProvider(DATA)
        updater = DatabaseUpdater(provider, DictBasedContentObject, self.db, logging)
        updater.update_provider()
        updater.update_database()
        config = FeedConfig('test', 'A test Repository',
                            'http://localhost/repo/test',
                            logging)
        self.server = Server('http://localhost/repo', self.db)
        self.server.add_config(config)


    def request(self, **kwargs):
        req = CGIRequest(u'http://localhost/repo/test', **kwargs)
        req.stream = StringIO.StringIO()
        self.server.handle_request(req)
        req.stream.seek(0)
        return req.stream.read()
        
    def tearDown(self):
        del self.db
        del self.server

    def test_identify(self):
        response = self.request(verb=u'Identify')
        self.assertEquals('Status: 200 OK', response.splitlines()[0])
        self.assertTrue(
            '<repositoryName>A test Repository</repositoryName>' in response)

    def test_list_identifiers(self):
        response = self.request(verb=u'ListIdentifiers', metadataPrefix=u'oai_dc')
        self.assertEquals(response.count('<identifier>'), 3)

    def test_list_records(self):
        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc')
        self.assertEquals(response.count('<identifier>'), 3)
        self.assertEquals(response.count('<metadata>'), 3)

        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc', until='2004-01-01T14:30:00Z')
        self.assertEquals(response.count('<identifier>'), 1)

        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc', until='2004-01-01T14:29:59Z')
        self.assertEquals(response.count('<identifier>'), 0)

        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc', from_='2008-01-01T14:30:00Z')
        self.assertEquals(response.count('<identifier>'), 1)

        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc', from_='2008-01-01T14:30:01Z')
        self.assertEquals(response.count('<identifier>'), 0)

        response = self.request(verb=u'ListRecords', metadataPrefix=u'oai_dc',
                                until='2004-01-01T14:30:00Z',
                                from_='2004-01-01T14:30:00Z')
        self.assertEquals(response.count('<identifier>'), 1)


    def test_list_metadata_formats(self):
        response = self.request(verb=u'ListMetadataFormats')
        self.assertTrue('<metadataPrefix>oai_dc</metadataPrefix>' in response)
        response = self.request(verb=u'ListMetadataFormats', identifier='oai:id:1')
        self.assertTrue('<metadataPrefix>oai_dc</metadataPrefix>' in response)

    def test_get_record(self):
        response = self.request(verb=u'GetRecord', identifier=u'oai:id:1',
                                metadataPrefix=u'oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:1</identifier>' in response)
        
        response = self.request(verb=u'GetRecord', identifier=u'oai:id:3',
                                metadataPrefix=u'oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:3</identifier>' in response)
        
        response = self.request(verb=u'GetRecord', identifier=u'oai:id:2',
                                metadataPrefix=u'oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:2</identifier>' in response)

        response = self.request(verb=u'GetRecord', identifier=u'invalid"id',
                                metadataPrefix=u'oai_dc')
        self.assertTrue('code="idDoesNotExist"' in response)

    def test_disallowed_set_record(self):
        config = FeedConfig('test', 'A test Repository',
                            'http://localhost/repo/test',
                            logging,
                            sets_disallowed=[u'datasets'])
        self.server = Server('http://localhost/repo', self.db)
        self.server.add_config(config)
        # identifier 2 should not be in the identifier list
        response = self.request(verb=u'ListIdentifiers', metadataPrefix=u'oai_dc')
        self.assertFalse('<identifier>oai:id:2</identifier>' in response)
        response = self.request(verb=u'GetRecord', identifier=u'oai:id:2',
                                metadataPrefix=u'oai_dc')
        self.assertTrue('<error code="idDoesNotExist">oai:id:2</error>' in response)

    def test_deleted_set_record(self):
        config = FeedConfig('test', 'A test Repository',
                            'http://localhost/repo/test',
                            logging,
                            sets_deleted=[u'datasets'])
        self.server = Server('http://localhost/repo', self.db)
        self.server.add_config(config)
        # identifier 2 should be in the identifier list
        response = self.request(verb=u'ListIdentifiers', metadataPrefix=u'oai_dc')
        self.assertTrue('<identifier>oai:id:2</identifier>' in response)
        response = self.request(verb=u'GetRecord', identifier=u'oai:id:2',
                                metadataPrefix=u'oai_dc')
        self.assertTrue('<header status="deleted">' in response)
        self.assertFalse('<metadata>' in response)

class OAISQLiteTest(OAIBtreeTest):
    
    def get_database(self):
        return SQLiteDatabase()

   
def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(OAIBtreeTest))
    suite.addTest(makeSuite(OAISQLiteTest))
    return suite

if __name__ == '__main__':
    main(defaultTest='test_suite')
