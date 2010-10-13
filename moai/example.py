import os
import time
from datetime import datetime

from lxml import etree

from moai.utils import XPath

class ExampleContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.deleted = None
        self.data = None
        self.sets = None
        
    def update(self, path):
        doc = etree.parse(path)
        xpath = XPath(doc, nsmap={'x':'http://example.org/data'})
        
        self.root = doc.getroot()

        id = xpath.string('//x:id')
        self.id = 'oai:example-%s' % id
        self.modified = xpath.date('//x:modified')
        self.deleted = False
        
        self.sets = {u'example': {u'name':u'example',
                                  u'description':u'An Example Set'}}

        access = xpath.string('//x:access')
        if access == 'public':
            self.sets[u'public'] = {u'name':u'public',
                                    u'description':u'Public access'}
        elif access == 'private':
            self.sets[u'private'] = {u'name':u'private',
                                     u'description':u'Private access'}

        self.data = {'identifier': [u'http://example.org/data/%s' % id],
                     'title': [xpath.string('//x:title')],
                     'subject': xpath.strings('//x:subject'),
                     'description': [xpath.string('//x:abstract')],
                     'date': [xpath.string('//x:issued')]}
