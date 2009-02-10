import sys
import os
import time
import logging
from ConfigParser import ConfigParser


def get_moai_log():
    log = logging.getLogger('moai')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler('moai.log')
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)
    return log

def parse_config_file(filename, section):
    config = ConfigParser()
    config.read(filename)

    buildout_dir = os.path.dirname(filename)

    if not section in config.sections():
        return {}
    result = {}
    for option in config.options(section):
        value = config.get(section, option)
        result[option] = value.replace('${buildout:directory}',
                                       buildout_dir)
    return result

def get_duration(starttime):
    h,m,s = time.asctime(time.gmtime(time.time() - starttime)).split(' ')[-2].split(':')
    s = int(s)
    m = int(m)
    h = int(h)
    duration = '%s second%s' % (int(s), {1:''}.get(s, 's'))
    if m:
        duration = '%s minute%s, %s' % (int(m), {1:''}.get(m, 's'), duration)
    if h:
        duration = '%s hour%s, %s' % (int(h), {1:''}.get(h, 's'), duration)
    return duration

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
        rest = self.width - (len(msg) +2)
        self.write('%s %s%s'% (anim[self.animstate], msg, ' '*rest))
        self.animstate+=1
        if self.animstate == len(anim):
            self.animstate = 0



