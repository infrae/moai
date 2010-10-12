import os
import time
from datetime import datetime

from lxml import etree

from moai.content import XMLContentObject

class ExampleContent(XMLContentObject):

    def update(self, path, provider):
        self.provider = provider

        self.nsmap = {'ex':'http://example.org/data'}
        doc = etree.parse(path)
        self.root = doc.getroot()

        self.id = self.xpath('ex:id/text()', 'id', unicode, required=True)
        self.modified = datetime(*time.gmtime(os.path.getmtime(path))[:6])
        self.deleted = False
        self.sets = {}
        self.sets[u'example'] = {'name':u'example',
                                 'description':u'An Example Set'}
        
        self.data = {}
        for el in self.root:
            tagname = el.tag.split('}', 1)[-1]
            if tagname in ['author', 'asset']:
                value = {}
                for s_el in el:
                    text = s_el.text.strip().decode('utf8')
                    value[s_el.tag.split('}', 1)[-1]] = text
            else:
                value = el.text.strip().decode('utf8')
            self.data.setdefault(tagname,[]).append(value)


        if 'public' in self.data['access']:
            self.sets[u'public'] = {'name':u'public',
                                    'description':u'Public access'}
        elif 'private' in self.data['access']:
            self.sets[u'private'] = {'name':u'private',
                                     'description':u'Private access'}
