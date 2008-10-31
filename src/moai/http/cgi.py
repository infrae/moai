
from zope.interface import implements

from moai.interfaces import IServerRequest

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

