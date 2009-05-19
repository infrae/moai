from StringIO import StringIO

from zope.interface import implements
import cherrypy
from cherrypy import HTTPError, HTTPRedirect
from cherrypy.lib.static import serve_file

from moai.interfaces import IServerRequest

class CherryPyRequest(object):
    """This is a request object that can be used in a CherryPy environment.
    It implements :ref:`IServerRequest` interface.
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
        raise HTTPRedirect(url)

    def send_file(self, path, mimetype):
        """Send the file located at 'path' back to the user
        """
        return serve_file(path, mimetype, "attachment")

    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        return self._kw

    def write(self, data, mimetype):
        """Write data back to the client
        """
        cherrypy.response.headers['Content-Type'] = mimetype
        cherrypy.response.headers['Content-Length'] = len(data)
        return data

    def send_status(self, code, msg='', mimetype='text/plain'):
        raise HTTPError(code.split(' ')[0], message=msg)

class MOAICherry(object):

    def __init__(self, name, server):
        self.server = server
        self.name = name

    @cherrypy.expose
    def default(self, *args, **kw):
        if not args:
            raise HTTPRedirect('/%s' % self.name)
        if args[0] != self.name:
            raise HTTPError(404)
        args = args[1:]
        url = self.server.base_url + '/'.join(args)
        req = CherryPyRequest(url, **kw)
        return self.server.handle_request(req)

        
def start_server(host, port, threads, name, server):

    cherrypy.quickstart(MOAICherry(name, server),
                        config=StringIO("""
[global]
server.socket_host = "%s"
server.socket_port = %s
server.thread_pool = %s
""" % (host, port, threads)))
