import sys

from zope.interface import implements

from moai.interfaces import IServerRequest

class CGIRequest(object):
    """This is a request object that can be used in a CGI environment.
    Note that this is not to be used in production scenarios, it's main
    use is documentation, and as a backend used in the unittests
    This class implements :ref:`IServerRequest` interface.
    """
    implements(IServerRequest)

    def __init__(self, url, **kw):
        self.stream = sys.stdout
        self._url = url
        self._kw = kw
        if 'from_' in self._kw:
            self._kw['from'] = self._kw['from_']
            del self._kw['from_']

    def url(self):
        return self._url
    
    def redirect(self, url):
        """Redirect to this url
        """
        self.stream.write('Status: 403 Redirect\n')
        self.stream.write('Location: %s\n\n' % url)

    def send_file(self, path, mimetype):
        """Send the file located at 'path' back to the user
        """
        fp = open(path, 'rb')
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        self.stream.write('Status: 200 OK\n')
        self.stream.write('Content-Type: %s\n' % mimetype)
        self.stream.write('Content-Length: %s\n\n' % size)
        self.stream.write(fp.read())
        fp.close()

    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        return self._kw

    def write(self, data, mimetype):
        """Write data back to the client
        """
        self.stream.write('Status: 200 OK\n')
        self.stream.write('Content-Type: %s\n' % mimetype)
        self.stream.write('Content-Length: %s\n\n' % len(data))
        self.stream.write(data)

    def send_status(self, code, msg='', mimetype='text/plain'):
        self.stream.write('Status: %s\n' % code)
        self.stream.write('Content-Type: %s\n' % mimetype)
        self.stream.write('Content-Length: %s\n\n' % len(msg))
        self.stream.write(msg)
