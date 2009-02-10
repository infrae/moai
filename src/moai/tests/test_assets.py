import os
import tempfile
import logging
import shutil
import StringIO
from unittest import TestCase, TestSuite, makeSuite, main

from moai.provider.list import ListBasedContentProvider
from moai.content import DictBasedContentObject
from moai.update import DatabaseUpdater
from moai.database.btree import BTreeDatabase
from moai.server import Server, FeedConfig
from moai.http.cgi import CGIRequest
from moai.tests.test_database import DATA
from moai.core import MOAI

class AssetTest(TestCase):

    def setUp(self):
        # init moai, so metadata formats get registered
        m = MOAI(logging, debug=True)

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

        self.asset_dir = os.path.join(tempfile.gettempdir(),
                                 'id:2')
        if not os.path.isdir(self.asset_dir):
            os.mkdir(self.asset_dir)
        fp = open(os.path.join(self.asset_dir, 'test.txt'), 'w')
        fp.write('This is an asset')
        fp.close()
        
        
    def tearDown(self):
        del self.db
        del self.server

        if os.path.isfile(self.asset_dir):
            shutil.rmtree(self.asset_dir)

    def request(self, url, **kwargs):
        req = CGIRequest('http://localhost/repo/test' + url, **kwargs)
        req.stream = StringIO.StringIO()
        self.server.handle_request(req)
        req.stream.seek(0)
        return req.stream.read()

    def test_asset_200(self):
        # downloading this asset should work
        response = self.request('/asset/id:2/test.txt')
        self.assertEquals(response.splitlines()[0],
                          'Status: 200 OK')
    def test_asset_404(self):
        # a non existing asset should return a 404
        response = self.request('/asset/id:2/foo')
        self.assertEquals(response.splitlines()[0],
                          'Status: 404 File not Found')
    def test_asset_403(self):
        # let's make a feed which does not include id:2
        # because it disallows everythin in the datasets set
        config = FeedConfig('test', 'A test Repository',
                            'http://localhost/repo/test',
                            logging,
                            sets_disallowed=[u'datasets'])
        
        self.server = Server('http://localhost/repo', self.db)
        self.server.add_config(config)
        
        # first we'll test that the record is not in the feed
        response = self.request('', verb='ListIdentifiers', metadataPrefix='oai_dc')
        self.assertEquals(response.count('<identifier>'), 2)
        self.assertFalse('<identifier>oai:id:2</identifier>' in response)

        # now, we when we get the asset, it should return a forbidden
        response = self.request('/asset/id:2/test.txt')
        self.assertEquals(response.splitlines()[0],
                          'Status: 403 Forbidden')

        
   
def test_suite():
    return TestSuite((makeSuite(AssetTest), ))


if __name__ == '__main__':
    main(defaultTest='test_suite')
    pass
