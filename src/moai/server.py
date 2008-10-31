import os

from zope.interface import implements

from moai.interfaces import IServer, IServerConfig
from moai.oai import OAIServerFactory

class Server(object):

    implements(IServer)

    def __init__(self, base_url, db):
        self.base_url = base_url
        self._db = db
        self._configs = {}

    def add_config(self, config):
        self._configs[config.id] = config

    def get_config(self, id):
        return self._configs.get(id)

    def download_asset(self, url, config):
        assetpath = url.split('/asset/')[-1]
        return self.backend.sendfile(assetpath, 'apllication/binary')

    def allow_download(self, url, config):
        return True

    def is_asset_url(self, url, config):
        if url.startswith('asset/'):
            return True
        return False
            
    def handle_request(self, req):

        if not req.url().startswith(self.base_url):
            return req.send_status('500 Internal Server Error',
                 'The url "%s" does not start with base url "%s".' % (req.url(),
                                                                      self.base_url))
        url = req.url()[len(self.base_url):]
        
        if url.startswith('/'):
            url = url[1:]
        if url.endswith('/'):
            url = url[:-1]
                                   
        urlparts = url.split('/')                           

        if len(urlparts) == 0:
            return req.send_status('500 Internal Server Error',
                 'No server was selected, please append server name to url.')
        
        config_name = urlparts.pop(0)
        config = self.get_config(config_name)

        if config is None:
            return req.send_status('404 File Not Found',
                 'No server with name "%s" exists' % config_name)
            
        url = '/'.join(urlparts)

        if self.is_asset_url(url, config):
            if self.allow_download(url, config):
                return self.download_asset(url, config)
            else:
                return req.send_status('403 Forbidden',
                                       'You are not allowed to download this asset')

        oai_server = OAIServerFactory(self._db, config)
        return req.write(oai_server.handleRequest(req.query_dict()), 'text/xml')

class ServerConfig(object):

    implements(IServerConfig)

    def __init__(self,
                 id,
                 repository_name,
                 base_url,
                 log,
                 admin_emails = [],
                 metadata_prefixes = ['oai_dc'],
                 batch_size = 100,
                 content_type = None,
                 sets_allowed = [],
                 sets_disallowed = [],
                 filter_sets = [],
                 delay = 0):
        
        self.id = id
        self.name = repository_name
        self.url = base_url
        self.log = log
        self.admins = admin_emails
        self.metadata_prefixes = metadata_prefixes
        self.batch_size = batch_size
        self.content_type = content_type
        self.sets_allowed = sets_allowed
        self.sets_disallowed = sets_disallowed
        self.filter_sets = filter_sets
        self.delay = delay

    def get_oai_id(self, internal_id):
        return 'oai:%s' % internal_id

    def get_internal_id(self, oai_id):
        return oai_id[4:]

    def get_setspec_id(self, internal_set_id):
        return 'set_%s' % internal_set_id

    def get_internal_set_id(self, oai_setspec_id):
        return oai_setspec_id[4:]

