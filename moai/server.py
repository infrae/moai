"""
moai.server
===========

The Server module contains implementations
of :ref:`IServer` and :ref:`IFeedConfig`.

"""
import os
import tempfile

from zope.interface import implements
import oaipmh.error

from moai.interfaces import IServer, IFeedConfig
from moai.oai import OAIServerFactory, OAIServer

class Server(object):
    """This is the default implementation of the
    :ref:`IServer` interface. 

    Developers might want to subclass this, to provide custom
    asset handling in their implementation.
    """

    implements(IServer)

    def __init__(self, base_url, db, config):
        self.base_url = base_url
        self._db = db
        self._config = config

    def download_asset(self, req, url, config):
        """Download an asset
        """
        url = url.lstrip('/')
        asset_url = url.split('asset/')[-1]
        id, filename = asset_url.split('/')

        for asset in self._db.get_assets(id):
            if (asset['filename'] == filename or
                asset['md5'] == filename):
                break
        else:
            return req.send_status('404 File not Found',
                                   'The asset "%s" does not exist' % filename)
            
        assetpath = config.get_asset_path(id, asset)

        if not os.path.isfile(assetpath):
            return req.send_status('404 File not Found',
                                   'The asset file "%s" does not exist' % filename)

        
        return req.send_file(assetpath,
                             asset['mimetype'].encode('ascii'))

    def allow_download(self, url, config):
        """Returns a boolean indicating if it is okay to download an
        asset or not. 

        By examining the url, the id of the oai record can be found, and
        thus the metadata can be accessed. This metadata could have settings
        to indicate that the asset is private and should not be downloaded

        """
        
        url = url.lstrip('/')
        asset_url = url.split('asset/')[-1]
        id, filename = asset_url.split('/')
        
        oai_server = OAIServer(self._db, config)
        try:
            header, metadata, descriptio = oai_server.getRecord(
                'oai_dc', config.get_oai_id(id))
        except oaipmh.error.IdDoesNotExistError:
            # record is not in the oai feed, don't download
            return False
        if header.isDeleted():
            # record has deleted status, don't download
            return False

        return True

    def is_asset_url(self, url, config):
        """Returns a boolean indicating if this is a url
        for downloading an asset or not
        """
        
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
        
            
        url = '/'.join(urlparts)

        if self.is_asset_url(url, self._config):
            if self.allow_download(url, self._config):
                return self.download_asset(req, url, self._config)
            else:
                return req.send_status('403 Forbidden',
                                       'You are not allowed to download this asset')

        oai_server = OAIServerFactory(self._db, self._config)
        return req.write(oai_server.handleRequest(req.query_dict()), 'text/xml')

class FeedConfig(object):
    """The feedconfig object contains all the settings for a specific
    feed. It implements the :ref:`IFeedConfig` interface.
    """

    implements(IFeedConfig)

    def __init__(self,
                 repository_name,
                 base_url,
                 admin_emails = [],
                 metadata_prefixes = ['oai_dc'],
                 batch_size = 100,
                 content_type = None,
                 sets_needed = [],
                 sets_allowed = [],
                 sets_disallowed = [],
                 sets_deleted = [],
                 filter_sets = [],
                 delay = 0,
                 base_asset_path=None):
        
        self.name = repository_name
        self.url = base_url
        self.admins = admin_emails
        self.metadata_prefixes = metadata_prefixes
        self.batch_size = batch_size
        self.content_type = content_type
        self.sets_needed = sets_needed
        self.sets_allowed = sets_allowed
        self.sets_disallowed = sets_disallowed
        self.sets_deleted = sets_deleted
        self.filter_sets = filter_sets
        self.delay = delay
        self.base_asset_path = base_asset_path or tempfile.gettempdir()
