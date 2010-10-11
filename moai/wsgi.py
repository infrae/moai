from StringIO import StringIO

from zope.interface import implements
from webob import Request, Response

from moai.interfaces import IServerRequest

class WSGIRequest(object):
    """This is a request object that can be used in a WSGI environment.
    It implements :ref:`IServerRequest` interface.
    """
    implements(IServerRequest)

    def __init__(self, request):
        self._req = request

    def url(self):
        return self._req.url
    
    def redirect(self, url):
        """Redirect to this url
        """
        response = Response()
        response.status = 302
        response.location = url
        return response

    def send_file(self, path, mimetype):
        """Send the file located at 'path' back to the user
        """
        response = Response(content_type=mimetype,
                            conditional_request=True)
        response.app_iter = FileIterable(path)
        response.content_length = os.path.getsize(path)
        response.last_modified = os.path.getmtime(path)
        response.etag = '%s-%s-%s' % (response.last_modified,
                                      response.content_length,
                                      hash(path))
        return response
    
    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        return dict(self._req.GET)

    def write(self, data, mimetype):
        """Write data back to the client
        """
        response = Response()
        response.content_type = mimetype
        response.body = data
        return response

    def send_status(self, code, msg='', mimetype='text/plain'):
        response = Response()
        response.content_type = mimetype
        response.status = code
        response.body = msg
        raise response


class MOAIWSGIApp(object):
    # the wsgi app, calls the IServer with the IServerRequest 
    def __init__(self, name, server):
        self.name = name
        self.server = server

    def __call__(self, environ, start_response):
        request = Request(environ)
        return self.server.handle_request(WSGIRequest(request))

def app_factory(global_config, name, server):
    # WSGI APP Factory
    return MOAIWSGIApp(name, server)

class FileIterable(object):
    # Helper objects to stream asset files
    def __init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop
    def __iter__(self):
        return FileIterator(self.filename, self.start, self.stop)
    def app_iter_range(self, start, stop):
        return self.__class__(self.filename, start, stop)

class FileIterator(object):
    chunk_size = 4096
    def __init__(self, filename, start, stop):
        self.filename = filename
        self.fileobj = open(self.filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = stop - start
        else:
            self.length = None
    def __iter__(self):
        return self
    def next(self):
        if self.length is not None and self.length <= 0:
            raise StopIteration
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        if self.length is not None:
            self.length -= len(chunk)
            if self.length < 0:
                # Chop off the extra:
                chunk = chunk[:self.length]
        return chunk
