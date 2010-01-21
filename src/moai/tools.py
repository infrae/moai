import sys
import time
import logging
import logging.handlers
import datetime
from optparse import OptionParser

from moai.core import MOAI, __version__                   
from moai.utils import (get_moai_log,
                        parse_config_file,
                        get_duration,
                        ProgressBar)
                 
def update_database(configfile, configname, extension_modules):
    profile, options, moai = initialize('update_database', configfile, configname, extension_modules)
    
    updater = profile.get_database_updater()
    progress = ProgressBar()
    error_count = 0
    starttime = time.time()

    from_date = None
    if options.from_date:
        if 'T' in options.from_date:
            from_date = datetime.datetime(*time.strptime(options.from_date,
                                                         '%Y-%m-%dT%H:%M:%S')[:6])
        else:
            from_date = datetime.datetime(*time.strptime(options.from_date,
                                                         '%Y-%m-%d')[:3])

    sys.stderr.write('Updating content provider..')
    count = 0    
    for id in updater.update_provider_iterate(from_date):
        if not options.quiet and not options.verbose:
            progress.animate('Updating content provider: %s' % id)
            count += 1

    if not options.quiet and not options.verbose:
        progress.write('')
        print
        print >> sys.stderr, ('Content provider returned %s '
                              'new/modified objects' % count)
        print >> sys.stderr
    
    total = 0
    updated = []
    if options.debug:
        supress_errors = False
    else:
        supress_errors = True
    for count, total, id, error in updater.update_database_iterate(
                                                supress_errors=supress_errors):

        msg_count = ('%%0.%sd/%%s' % len(str(total))) % (count, total)
        if not error is None:
            error_count += 1
            profile.log.error('%s %s' % (msg_count, error.logmessage()))
            if options.debug:
                print >> sys.stderr, '\n'
                import traceback
                traceback.print_tb(error.tb)
                print error.err, error.detail
                sys.exit(1)
            continue
        elif options.quiet:
            pass
        elif options.verbose:
            profile.log.info('%s Added %s'  % (msg_count, id))
        else:
            progress.tick(count, total)
        updated.append(id)

    if not options.quiet and not options.verbose:
        print >> sys.stderr, '\n'

    duration = get_duration(starttime)
    msg = 'Updating database with %s objects took %s' % (total, duration)
    profile.log.info(msg)
    if not options.verbose and not options.quiet:
        print >> sys.stderr, msg

    if error_count:
        multi = ''
        if error_count > 1:
            multi = 's'
        msg = '%s error%s occurred during updating' % (error_count, multi)
        profile.log.warning(msg)
        if not options.verbose and not options.quiet:
            print >> sys.stderr, msg

    plugin_names = moai.get_plugin_names()
    configured_plugins = profile.config.get('plugins', [])
    plugin_names = [n for n in plugin_names if n in configured_plugins]
   
    if len(plugin_names) == 0:
        sys.exit(0)
    
    for num, name in enumerate(plugin_names):
        num += 1
        msg = 'Running plugin %s/%s: %s' % (num,
                                            len(plugin_names),
                                            name)
        if not options.verbose and not options.quiet:
            print >> sys.stderr, msg
        profile.log.info(msg)
        config = parse_config_file(configfile, name)

        plugin = moai.get_plugin(name)(updater.db,
                                       profile.log,
                                       config)
        try:
            plugin.run(updated)
        except Exception, err:
            errname = type(err).__name__
            if not options.quiet:
                print >> sys.stderr, '-> %s: %s' % (errname, err)
            profile.log.error('Error while running plugin %s:\n%s' % (name, err))
            if options.debug:
                raise
            
def start_development_server(configfile, configname, extension_modules):
    profile, options, moai = initialize('start_server', configfile, configname, extension_modules)
    profile.start_development_server()

def initialize(script, configfile, configname, extension_modules):
    usage = "usage: %prog [options]"
    version = "%%proc %s" % __version__

    parser = OptionParser(usage, version=version)

    parser.add_option("-v", "--verbose", dest="verbose",
                      help="print logging at info level",
                      action="store_true")
    parser.add_option('-d', '--debug', dest='debug',
                      help="print traceback and quit on error",
                      action='store_true')
    parser.add_option("-q", "--quiet", dest="quiet",
                      help="be quiet, do not output and info",
                      action="store_true")
    parser.add_option("", "--config", dest="config",
                      help="do not use default config profile (%s)" % configname,
                      action="store")
    
    if script == 'update_database':
        parser.add_option("", "--date", dest="from_date",
                      help="Only update database from a specific date",
                      action="store")
        
    options, args = parser.parse_args()

    if options.config:
        configname = options.config
        
    log = get_moai_log()

    moai = MOAI(log,
                options.verbose,
                options.debug)

    for module_name in extension_modules:
        moai.add_extension_module(module_name)
    config = moai.get_configuration(configname)
    if config is None:
        msg = 'Unknown configuration: "%s", exiting..' % configname
        log.error(msg)
        print >> sys.stderr, msg
        sys.exit(1)

    log.info('Initializing configuration profile "%s"' % configname)
    profile = config(log,
                     parse_config_file(configfile, configname))
    return profile, options, moai

    
