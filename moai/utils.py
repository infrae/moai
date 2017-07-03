import sys
import datetime
import time
import logging
import logging.handlers
import six


def get_moai_log():
    log = logging.getLogger('moai')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler('moai.log')
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)
    return log

def get_duration(starttime):
    h,m,s = time.asctime(
        time.gmtime(time.time() - starttime)).split(' ')[-2].split(':')
    s = int(s)
    m = int(m)
    h = int(h)
    duration = '%s second%s' % (int(s), {1:''}.get(s, 's'))
    if m:
        duration = '%s minute%s, %s' % (int(m), {1:''}.get(m, 's'), duration)
    if h:
        duration = '%s hour%s, %s' % (int(h), {1:''}.get(h, 's'), duration)
    return duration

def check_type(object,
               expected_type,
               unicode_keys=False,
               unicode_values=False,
               recursive=False,
               prefix='',
               suffix=''):

    object_type = type(object)
    if not isinstance(object, expected_type):
        
        raise TypeError(('%s expected "%s", got "%s" %s' % (
            prefix,
            expected_type.__name__,
            object.__class__.__name__,
            suffix)).strip())
    if unicode_keys and object_type is dict:
        check_type(object.keys(),
                   list,
                   unicode_values=True,
                   prefix=prefix,
                   suffix=suffix)
    if unicode_values and object_type is dict:
        check_type(list(object.values()),
                   list,
                   unicode_keys=unicode_keys,
                   unicode_values=True,
                   recursive=recursive,
                   prefix=prefix,
                   suffix=suffix)
    if unicode_values and object_type is list:
        for stuff in object:
            if six.PY2:
                if isinstance(stuff, str):
                    raise TypeError(('%s contains non unicode string "%s" %s' % (
                        prefix,
                        stuff,
                        suffix)).strip())
            if recursive:
                if isinstance(stuff, list):
                    check_type(stuff,
                               list,
                               unicode_keys=unicode_keys,
                               unicode_values=True,
                               recursive=True,
                               prefix=prefix,
                               suffix=suffix)
                if isinstance(stuff, dict):
                    check_type(stuff,
                               dict,
                               unicode_keys=unicode_keys,
                               unicode_values=True,
                               recursive=True,
                               prefix=prefix,
                               suffix=suffix)

class XPath(object):
    def __init__(self, doc, nsmap={}):
        self.doc = doc
        self.nsmap = nsmap

    def string(self, xpath):
        return (self.strings(xpath) or [None])[0]

    def strings(self, xpath):
        result = []
        for stuff in self.doc.xpath(xpath, namespaces=self.nsmap):
            if isinstance(stuff, str):
                result.append(stuff.strip().decode('utf8'))
            elif isinstance(stuff, six.text_type):
                # convert to real unicode object, not lxml proxy
                result.append(six.text_type(stuff.strip()))
            elif hasattr(stuff, 'text'):
                if isinstance(stuff.text, str):
                    v = stuff.text.strip()
                    if six.PY2:
                        v = v.decode('utf8')
                    result.append(v)
                elif isinstance(stuff.text, six.text_type):
                    # convert to real unicode object, not lxml proxy
                    result.append(six.text_type(stuff.text.strip()))
        return result
    
    def number(self, xpath):
        return (self.numbers(xpath) or [None])[0]

    def numbers(self, xpath):
        result = []
        for value in self.strings(xpath):
            try:
                value = int(value)
                result.append(value)
            except:
                try:
                    value = float(value)
                    result.append(value)
                except:
                    raise ValueError('Unknown number format: %s' % value)
        return result

    def boolean(self, xpath):
        return (self.booleans(xpath) or [None])[0]

    def booleans(self, xpath):
        result = []
        for value in self.strings(xpath):
            if value.lower() in ['true', 'yes']:
                result.append(True)
            elif value.lower() in ['false', 'no']:
                result.append(False)
            else:
                raise ValueError('Unknown boolean format: %s' % value)
        return result

    def date(self, xpath):
        return (self.dates(xpath) or [None])[0]

    def dates(self, xpath):
        result = []
        for value in self.strings(xpath):
            if 'T' in value:
                if value.endswith('Z'):
                    value = value[:-1] + ' UTC'
                    fmt = '%Y-%m-%dT%H:%M:%S %Z'
                else:
                    fmt = '%Y-%m-%dT%H:%M:%S'
            elif value.count('-') == 2:
                fmt = '%Y-%m-%d'
            elif value.count('/') == 2:
                fmt = '%Y/%m/%d'
            else:
                fmt = '%Y%m%d'
            try:
                result.append(datetime.datetime.strptime(value, fmt))
            except ValueError:
                raise ValueError('Unknown date format: %s' % value)
        return result

    def tag(self, xpath):
        return (self.tags(xpath) or [None])[0]

    def tags(self, xpath):
        result = []
        for stuff in self.doc.xpath(xpath, namespaces=self.nsmap):
            if hasattr(stuff, 'tag'):
                if '}' in stuff.tag:
                    v = stuff.tag.split('}', 1)[1]
                    if six.PY2:
                        v = v.decode('utf8')
                    result.append(v)
                else:
                    v = stuff.tag
                    if six.PY2:
                        v = v.decode('utf8')
                    result.append(v)
        return result
    
    def __call__(self, xpath):
        result = self.doc.xpath(xpath, namespaces=self.nsmap)
        return result


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
        if total:
            perc = '%0.1f' % (count / (total/100.0))
        else:
            perc = '0.0'
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



