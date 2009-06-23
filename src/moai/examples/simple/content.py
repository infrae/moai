import os
import time
from datetime import datetime

from lxml import etree

from moai.content import XMLContentObject

class SimpleDCContentObject(XMLContentObject):

    def update(self, path, provider):
        self.provider = provider
        self.nsmap = {'dc':'http://purl.org/dc/elements/1.1/'}
        doc = etree.parse(path)
        self.root = doc.getroot()

        self.id = self.xpath('dc:identifier[not(@scheme)]/text()',
                             'identifier', unicode, required=True)
        self.content_type = u'publication'
        self.label = self.xpath('dc:title/text()',
                                'label', unicode, required=True)
        self.is_set = False
        
        self.when_modified = datetime(*time.gmtime(os.path.getmtime(path))[:6])
        self.deleted = False
        self.sets = []
        self.sets.extend(self.xpath('dc:subject/text()',
                                    'subject', unicode, multi=True))

        self._assets = [{u'filename': u'%s.pdf' % self.id,
                         u'url': u'asset/%s/%s.pdf' % (self.id, self.id),
                         u'absolute_uri': u'',
                         u'mimetype': u'application/pdf',
                         u'md5': u'',
                         u'metadata': {}}]


        
        self._fields = self.set_publication_fields()
        
    def set_publication_fields(self):
        fields = {
            u'description': self.xpath('dc:description/text()',
                                       'description', unicode, multi=True),
            u'title': [self.label],
            u'date': self.xpath('dc:date/text()',
                                'date', datetime, multi=True),
            u'subject': self.xpath('dc:subject/text()',
                                   'subject', unicode, multi=True),
            u'identifier': [self.id],
            u'language': self.xpath('dc:lanauge/text()',
                                    'language', unicode, multi=True),
            u'type': self.xpath('dc:type/text()',
                                'type', unicode, multi=True),
            u'url': self.xpath('dc:identifier[@scheme="dcterms:URI"]/text()',
                               'identifier', unicode, multi=True),
            u'author': self.xpath('dc:creator/text()',
                                  'creator', unicode, multi=True),
        }
        
        if fields['date']:
            # fields should always be unicode
            fields['date'] = [unicode(fields['date'][0].isoformat())]

        return fields
    
    def get_assets(self):
        return self._assets
