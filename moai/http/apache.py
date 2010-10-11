import sys
import os
import logging

from zope.interface import implements

try:
    from mod_python import apache
    from mod_python import util as apache_util
except ImportError:
    # mod_python is not installed, or we're not running
    # inside the Apache server
    pass

from moai.interfaces import IServerRequest

class ModPythonRequest(object):
    """This is a request object that can be used in an
    Apache mod_python environment.
    This class implements :ref:`IServerRequest` interface.
    """
    implements(IServerRequest)

    def __init__(self, req):
        self.req = req

    def url(self):
        return self.req.uri
    
    def redirect(self, url):
        """Redirect to this url
        """
        return apache.util.redirect(self.req, url)

    def send_file(self, path, mimetype):
        """Send the file located at 'path' back to the user
        """
        self.req.content_type = mimetype
        self.req.headers_out['Accept-Ranges'] = 'none'
        self.req.sendfile(path)
        return apache.OK
    
    def query_dict(self):
        """Return a dictionary with QueryString values of the
        request
        """
        qs = apache_util.FieldStorage(self.req)
        kw = {}
        for val in qs.list:
            kw[val.name] = qs.getfirst(val.name)
        return kw

    def write(self, data, mimetype):
        """Write data back to the client
        """
        self.req.content_type = mimetype
        self.req.write(data)

    def send_status(self, code, msg='', mimetype='text/plain'):
        code = int(code.split(' ')[0])
        self.req.log_error('MOAI %s -> %s' % (code, msg))
        return {200: apache.OK,
                404: apache.HTTP_NOT_FOUND,
                403: apache.HTTP_FORBIDDEN,
                500: apache.HTTP_INTERNAL_SERVER_ERROR}[code]

def handler(req):
    # This function should be Called by Apache
    from moai.core import MOAI
    import moai.utils
    
    configname = req.subprocess_env['MOAI_PROFILE']
    config = moai.utils.parse_config_file(
        req.subprocess_env['MOAI_CONFIGFILE'],
        configname)
    
    log = logging # XXX todo, should work with req.error_log
    moai = MOAI(log)
    
    for module_name in req.subprocess_env['MOAI_EXTENSIONS'].split():
        moai.add_extension_module(module_name)
        
    profile_class = moai.get_configuration(configname)
    profile = profile_class(log, config)

    server = profile.get_server()

    request = ModPythonRequest(req)
    result = server.handle_request(request)
    if result is None:
        result = apache.OK

    return result

def generate_config(cfgfile, profile_name, extensions):
    from moai.core import MOAI
    import moai.utils
    log = logging

    config = moai.utils.parse_config_file(cfgfile, profile_name)
    moai = MOAI(log)
    for module_name in extensions:
        moai.add_extension_module(module_name)

    profile_class = moai.get_configuration(profile_name)
    profile = profile_class(log, config)
    server = profile.get_server()

    config = """
<location %s>

  SetHandler mod_python
  
  SetEnv MOAI_PROFILE "%s"
  SetEnv MOAI_CONFIGFILE "%s"
  SetEnv MOAI_EXTENSIONS "%s"
  SetEnv PYTHON_EGG_CACHE "%s"  

  PythonHandler moai.http.apache::handler
  PythonDebug On

  PythonPath "%s"

</location>    
    """ % (server.base_url,
           profile_name,
           cfgfile,
           ' '.join(extensions),
           os.path.join(os.path.dirname(cfgfile), '.python_eggs'),
           sys.path)
    print config
    
    
