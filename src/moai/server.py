import os
from datetime import datetime
import cgi

import oaipmh
import oaipmh.metadata
import oaipmh.server
import oaipmh.error
from zope.interface import implements


from moai.interfaces import IServer, IServerConfig, IServerRequest
from moai.metadata import get_writer

class OAIServer(object):
    def __init__(self, db, config):
        self.db = db
        self.config = config

    def identify(self):
        return oaipmh.common.Identify(
            repositoryName=self.config.name,
            baseURL=self.config.url,
            protocolVersion='2.0',
            adminEmails=self.config.admins,
            earliestDatestamp=datetime(2001, 1, 1, 10, 00),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'])
    
    def listSets(self, cursor=0, batch_size=20):
        for set in self.db.oai_sets(cursor, batch_size):
            oai_id = self.config.get_setspec_id(set['id'])
            yield [oai_id, set['name'], set['description']]

    def listRecords(self, metadataPrefix, set=None, from_=None, until=None,
                    cursor=0, batch_size=10):
        
        self._checkMetadataPrefix(metadataPrefix)
        for record in self._listQuery(set, from_, until, cursor, batch_size):
            header, metadata = self._createHeaderAndMetadata(record)
            yield header, metadata, None

    def listIdentifiers(self, metadataPrefix, set=None, from_=None, until=None,
                        cursor=0, batch_size=10):
        
        self._checkMetadataPrefix(metadataPrefix)
        for record in self._listQuery(set, from_, until, cursor, batch_size):
            yield self._createHeader(record)

    def _checkMetadataPrefix(self, metadataPrefix):
        if metadataPrefix not in self.config.metadata_prefixes:
            raise oaipmh.error.CannotDisseminateFormatError

    def _createHeader(self, record):
        oai_id = self.config.get_oai_id(record['record']['id'])
        datestamp = record['record']['when_modified']
        sets = record['sets']
        deleted = record['record']['deleted']
        return oaipmh.common.Header(oai_id, datestamp, sets, deleted)

    def _createHeaderAndMetadata(self, record):
        header = self._createHeader(record)
        metadata = oaipmh.common.Metadata(record['metadata'])
        metadata.record = record
        return header, metadata
    
    def _listQuery(self, set, from_, until, 
                   cursor, batch_size, identifier=None):

        if identifier:
            identifier = self.config.get_internal_id(identifier)
        if set:
            set = self._get_internal_set_id(set)
            
        now = datetime.now()
        if until != None and until > now:
            # until should never be in the future
            until = now
            
        if self.config.delay:
            # subtract delay from until_ param, if present
            if until is None:
                until = datetime.now()
            until = until.timetuple()
            ut = time.mktime(until)-self.filter_data.delay
            until = datetime.fromtimestamp(ut)
            
        if set is None:
            sets = []
        else:
            sets = [set]

        sets += self.config.sets_allowed
        filtersets = self.config.filter_sets
        notsets = self.config.sets_disallowed    
        
        return self.db.oai_query(offset=cursor,
                                 batch_size=batch_size,
                                 sets=sets,
                                 not_sets=notsets,
                                 filter_sets=filtersets,
                                 from_date=from_,
                                 until_date=until,
                                 identifier=identifier
                                 )

def OAIServerFactory(db, config):
    metadata_registry = oaipmh.metadata.MetadataRegistry()
    for prefix in config.metadata_prefixes:
        metadata_registry.registerWriter(prefix,
                                         get_writer(prefix, config, db))
            
    return oaipmh.server.BatchingServer(
        OAIServer(db, config),
        metadata_registry=metadata_registry,
        resumption_batch_size=config.batch_size
        )

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
                                                                      base_url))
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
                return req.send_status('403 Not Allowed')

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


class CGIRequest(object):
    """This is a request object that can be used in a CGI environment.
    Note that this is not to be used in production scenarios, it's main
    use is documentation, and as a backend used in the unittests
    """
    implements(IServerRequest)

    def __init__(self, url, **kw):
        self._url = url
        self._kw = kw

    def url(self):
        return self._url
    
    def redirect(self, url):
        """Redirect to this url
        """
        print 'Status: 403 Redirect'
        print 'Location: %s' % url
        print

    def send_file(self, path, mimetype):
        """Send the file located at 'path' back to the user
        """
        fp = open(path, 'rb')
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        print 'Status: 200 OK'
        print 'Content-Type: %s' % mimetype
        print 'Content-Length: %s' % size
        print
        print fp.read()
        fp.close()

    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        return self._kw

    def write(self, data, mimetype):
        """Write data back to the client
        """
        print 'Status: 200 OK'
        print 'Content-Type: %s' % mimetype
        print 'Content-Length: %s' % len(data)
        print
        print data

    def send_status(self, code, msg='', mimetype='text/plain'):
        print 'Status: %s' % code
        print 'Content-Type: %s' % mimetype
        print 'Content-Length: %s' % len(msg)
        print
        print msg
