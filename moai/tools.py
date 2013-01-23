import sys
import os
import time
import datetime
import pkg_resources
from pkg_resources import iter_entry_points
import ConfigParser

from optparse import OptionParser

from moai.utils import (get_duration,
                        get_moai_log,
                        ProgressBar)
from moai.database import SQLDatabase

VERSION = pkg_resources.working_set.by_key['moai'].version
                 
def update_moai():
    usage = "usage: %prog [options] profilename"
    version = "%%prog %s" % VERSION

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
                      help="specify settings file",
                      action="store")
    parser.add_option("", "--date", dest="from_date",
                      help="Only update database from a specific date",
                      action="store")
        
    options, args = parser.parse_args()
    if not len(args):
        profile_name = 'default'
    else:
        profile_name = args[0]
    if options.config:
        config_path = options.config
    else:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0]))),
            'settings.ini')
    if not os.path.isfile(config_path):
        sys.stderr.write('No config_path file found at %s,\n'
                         'Start script from other directory '
                         'or use --config option\n''' % config_path)
        sys.exit(1)
    configfile = ConfigParser.ConfigParser()
    configfile.read(config_path)
    profiles = []
    config = {}
    for section in configfile.sections():
        if not configfile.has_option(section, 'use'):
            continue
        if configfile.get(section, 'use') == 'egg:moai':
            profiles.append(section.split(':', 1)[1])
        if profile_name == section.split(':', 1)[1]:
            for option in configfile.options(section):
                config[option] = configfile.get(section, option)
            
    if not profile_name in profiles:
        if profile_name == 'default':
            sys.stderr.write(
                'No profile name specified, use --help for more info\n')
        else:
            sys.stderr.write('unknown profile: %s\n' % profile_name)
        sys.stderr.write('(known profiles are: %s)\n' % ', '.join(profiles))
        sys.exit(1)

    if options.from_date:
        if 'T' in options.from_date:
            fmt = '%Y-%m-%dT%H:%M:%S'
        else:
            fmt = '%Y-%m-%d'
        from_date = datetime.datetime(
            *time.strptime(options.from_date, fmt)[:6])
    else:
        from_date = None

    database = SQLDatabase(config['database'])

    ContentClass = None
    for content_point in iter_entry_points(group='moai.content',
                                           name=config['content']):
        ContentClass = content_point.load()

    if ContentClass is None:
        sys.stderr.write('Unknown content class: %s\n' % (config['content'],))
        sys.exit(1)

    provider_name = config['provider'].split(':', 1)[0]
    provider = None
    for provider_point in iter_entry_points(group='moai.provider',
                                           name=provider_name):
        provider = provider_point.load()(config['provider'])

    if provider is None:
        sys.stderr.write('Unknown provider: %s\n' % (provider_name,))
        sys.exit(1)

    log = get_moai_log()
    provider.set_logger(log)

    progress = ProgressBar()
    starttime = time.time()

    sys.stderr.write('Updating content provider..')
    count = 0    
    for id in provider.update(from_date):
        if not options.quiet and not options.verbose:
            progress.animate('Updating content provider: %s' % id)
            count += 1

    if not options.quiet and not options.verbose:
        progress.write('')
        print
        print >> sys.stderr, ('Content provider returned %s '
                              'new/modified objects' % count)
        print >> sys.stderr
    
    total = provider.count()

    count = 0
    ignore_count = 0
    error_count = 0
    flush_threshold = int(config.get('forcedflush', '10000'))
    for content_id in provider.get_content_ids():
        count += 1
        try:
            raw_data = provider.get_content_by_id(content_id)
        except Exception, err:
            if options.debug:
                raise
            log.error('Error retrieving data %s from provider: %s' % (
                content_id, str(err)))
            error_count += 1
            progress.tick(count, total)
            continue

        try:
            content = ContentClass(provider)
            success = content.update(raw_data)
        except Exception, err:
            if options.debug:
                raise
            log.error('Error converting data %s to content: %s' % (
                content_id, str(err)))
            error_count += 1
            progress.tick(count, total)
            continue
        
        if success is False:
            log.warning('Ignoring %s' % content_id)
            ignore_count += 1
            progress.tick(count, total)
            continue
        
        try:
            database.update_record(content.id,
                                   content.modified,
                                   content.deleted,
                                   content.sets,
                                   content.metadata)
        except Exception, err:
            if options.debug:
                raise
            log.error('Error inserting %s into database: %s' % (
                content.id, str(err)))
            error_count += 1
            progress.tick(count, total)
            continue
            
        if count % flush_threshold == 0:
            log.info('Flushing database')
            database.flush()
        progress.tick(count, total)
        
    log.info('Flushing database')
    database.flush()
    duration = get_duration(starttime)
    print >> sys.stderr, ''
    msg = 'Updating database with %s objects took %s' % (total, duration)
    log.info(msg)
    if not options.verbose and not options.quiet:
        print >> sys.stderr, msg

    if error_count:
        msg = '%s error%s occurred during updating' % (
            error_count,
            {1: ''}.get(error_count, 's'))
        log.warning(msg)
        if not options.verbose and not options.quiet:
            print >> sys.stderr, msg

