import os

from webob import Request, Response

from moai.server import Server, FeedConfig
from moai.database import get_database

class WSGIRequest(object):
    """This is a request object that can be used in a WSGI environment.
    It implements :ref:`IServerRequest` interface.
    """
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
                            conditional_response=True)
        response.last_modified = os.path.getmtime(path)
        response.app_iter = FileIterable(path)
        with open(path) as f:
            response.body = f.read()
        response.content_length = os.path.getsize(path)
        # do not accept ranges, since this does not work reliable
        # with acrobat IE plugin
        response.headers['Accept-Ranges'] = 'none'
        return response
    
    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        args = dict(self._req.GET)
        args.update(dict(self._req.POST))
        return args

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
        response.status = int(code.split()[0])
        response.body = msg
        return response


class MOAIWSGIApp(object):
    # the wsgi app, calls the IServer with the IServerRequest 
    def __init__(self, server):
        self.server = server
        
    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.server.handle_request(WSGIRequest(request))
        return response(environ, start_response)

def app_factory(global_config,
                name,
                url,
                admin_email,
                database,
                formats,
                **kwargs):
    # WSGI APP Factory
    formats = formats.split()
    admin_email = admin_email.split()
    sets_deleted = kwargs.get('deleted_sets') or []
    if sets_deleted:
        sets_deleted = sets_deleted.split()
    sets_disallowed = kwargs.get('disallowed_sets', '') or []
    if sets_disallowed:
        sets_disallowed = sets_disallowed.split()
    sets_allowed = kwargs.get('allowed_sets', '') or []
    if sets_allowed:
        sets_allowed = sets_allowed.split()
    sets_needed = kwargs.get('needed_sets', '') or []
    if sets_needed:
        sets_needed = sets_needed.split()
    database = get_database(database, kwargs)
    feedconfig = FeedConfig(name,
                            url,
                            admin_emails=admin_email,
                            metadata_prefixes=formats,
                            sets_deleted=sets_deleted,
                            sets_disallowed=sets_disallowed,
                            sets_allowed=sets_allowed,
                            sets_needed=sets_needed,
                            extra_args=kwargs)
    server = Server(url, database, feedconfig)
    
    return MOAIWSGIApp(server)

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
