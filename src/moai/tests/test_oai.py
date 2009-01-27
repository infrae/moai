from unittest import TestCase, TestSuite, makeSuite, main
import logging
import StringIO

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.server import Server, FeedConfig
from moai.http.cgi import CGIRequest
from moai.tests.test_database import DATA

class OAITest(TestCase):

    def setUp(self):
        self.db = BTreeDatabase()
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
        req = CGIRequest('http://localhost/repo/test', **kwargs)
        req.stream = StringIO.StringIO()
        self.server.handle_request(req)
        req.stream.seek(0)
        return req.stream.read()
        
    def tearDown(self):
        del self.db
        del self.server

    def test_identify(self):
        response = self.request(verb='Identify')
        self.assertEquals('Status: 200 OK', response.splitlines()[0])
        self.assertTrue(
            '<repositoryName>A test Repository</repositoryName>' in response)

    def test_list_identifiers(self):
        response = self.request(verb='ListIdentifiers', metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 3)

    def test_list_records(self):
        response = self.request(verb='ListRecords', metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 3)
        self.assertEquals(response.count('<metadata>'), 3)

    def test_get_record(self):
        response = self.request(verb='GetRecord', identifier='oai:id:1',
                                metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:1</identifier>' in response)
        response = self.request(verb='GetRecord', identifier='oai:id:2',
                                metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:2</identifier>' in response)
        response = self.request(verb='GetRecord', identifier='oai:id:3',
                                metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 1)
        self.assertTrue('<identifier>oai:id:3</identifier>' in response)

        
   
def test_suite():
    return TestSuite((makeSuite(OAITest), ))


if __name__ == '__main__':
    main(defaultTest='test_suite')
