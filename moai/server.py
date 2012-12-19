"""
moai.server
===========

The Server module contains implementations
of :ref:`IServer` and :ref:`IFeedConfig`.

"""
import os
import tempfile

import oaipmh.error

from moai.oai import OAIServerFactory, OAIServer

class Server(object):
    """This is the default implementation of the
    :ref:`IServer` interface. 

    Developers might want to subclass this, to provide custom
    asset handling in their implementation.
    """
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
            return req.send_status(
                '404 File not Found',
                'The asset "%s" does not exist' % filename)
            
        if not os.path.isfile(asset['path']):
            return req.send_status(
                '404 File not Found',
                'The asset file "%s" does not exist' % filename)

        return req.send_file(asset['path'],
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
            header, metadata, description = oai_server.getRecord(
                'oai_dc', config.oai_id_prefix + id)
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
            return req.send_status(
                '500 Internal Server Error',
                'The url "%s" does not start with base url "%s".' % (
                req.url(), self.base_url))
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
    def __init__(self,
                 repository_name,
                 base_url,
                 admin_emails = None,
                 metadata_prefixes = None,
                 batch_size = 100,
                 content_type = None,
                 sets_needed = None,
                 sets_allowed = None,
                 sets_disallowed = None,
                 sets_deleted = None,
                 filter_sets = None,
                 extra_args = None):
        extra_args = extra_args or {}
        self.name = repository_name
        self.url = base_url
        self.admins = admin_emails or []
        self.metadata_prefixes = metadata_prefixes or ['oai_dc']
        self.batch_size = batch_size
        self.content_type = content_type
        self.sets_needed = set(sets_needed or [])
        self.sets_allowed = set(sets_allowed or [])
        self.sets_disallowed = set(sets_disallowed or [])
        self.sets_deleted = set(sets_deleted or [])
        self.filter_sets = set(filter_sets or [])
        self.delay = extra_args.get('delay', 0)
        self.base_asset_path = extra_args.get('base_asset_path',
                                              tempfile.gettempdir())
        self.oai_id_prefix = extra_args.get('oai_id_prefix', '')
        
