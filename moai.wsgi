import sys
import os
import site
import tempfile
import ConfigParser

os.environ['PYTHON_EGG_CACHE'] = tempfile.mkdtemp(prefix='moai-egg-cache-')

site.addsitedir(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             'lib',
                             'python%d.%d' % sys.version_info[:2],
                             'site-packages'))

from paste.deploy import loadapp

if sys.version_info >= (2, 6):
    from logging.config import fileConfig
else:
    from paste.script.util.logging_config import fileConfig

config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'settings.ini')
try:
    fileConfig(config_file)
except ConfigParser.NoSectionError:
    # no logging configured
    pass

application = loadapp('config:%s' % config_file)
