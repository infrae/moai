import sys
import logging
from optparse import OptionParser

from moai.core import MOAI, __version__

class ProgressBar(object):
    def __init__(self, stream=sys.stderr, width=80):
        self.out = stream
        self.width = width
        self.out.write('')
        self.oldperc = '0.0'
        self.animstate = 0

    def write(self,line):
        self.out.write('\r%s' % line)
        self.out.flush()
        
    def tick(self, count, total):
        perc = '%0.1f' % (count / (total/100.0))
        if perc == self.oldperc and not count == total:
            return
        self.oldperc = perc
        lstot = len(str(total))
        awidth = self.width - 10 - lstot
        arrow = ('=' * int(awidth * (float(perc)/100.0)-1))+'>'
        
        self.write(('%5s%%[%-'+str(awidth)+'s] %'+str(lstot)+'d') % (perc,
                                                                     arrow,
                                                                     count))

    def animate(self, msg):
        anim = ['|', '/', '-', '\\']
        self.write('%s %s'% (anim[self.animstate], msg))
        self.animstate+=1
        if self.animstate == len(anim):
            self.animstate = 0



def initialize(configname, extension_modules):
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

    options, args = parser.parse_args()
        
    log = logging.getLogger('moai')    
    moai = MOAI(log, options.verbose, options.debug)

    for module_name in extension_modules:
        moai.add_extension_module(module_name)
    
    config = moai.get_configuration(configname)
    if config is None:
        msg = 'Unknown configuration: "%s", exiting..' % configname
        log.error(msg)
        print >> sys.stderr, msg
        sys.exit(1)

    log.info('Initializing configuration profile "%s"' % configname)
    profile = config(log)
    return profile, options

    
def update_database(configname, extension_modules):
    profile, options = initialize(configname, extension_modules)
    updater = profile.datebaseUpdaterFactory()
    progress = ProgressBar()
    error_count = 0
    for count, total, id, error in updater.update():
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
        elif options.verbose:
            profile.log.info('%s Added %s'  % (msg_count, id))
        elif options.quiet:
            pass
        else:
            progress.tick(count, total)
            
    print >> sys.stderr, '\n'

   
def start_server(configname, extension_modules):
    profile, options = initialize(configname, extension_modules)
