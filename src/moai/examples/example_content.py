import os
import time
from datetime import datetime

from lxml import etree

from moai.content import XMLContentObject

class ExampleContentObject(XMLContentObject):

    def update(self, path, provider):
        self.provider = provider
        self.nsmap = {'ex':'http://example.org'}
        doc = etree.parse(path)
        self.root = doc.getroot()

        self.id = self.xpath('ex:id/text()', 'id', unicode, required=True)
        self.content_type = self.root.xpath('local-name()')
        if self.content_type == 'publication':
            self.label = self.xpath('ex:title/text()', 'label', unicode, required=True)
        else:
            self.label = self.xpath('ex:name/text()', 'label', unicode, required=True)
            
        self.when_modified = datetime(*time.gmtime(os.path.getmtime(path))[:6])
        self.deleted = False
        self.sets = self.xpath('ex:set/@ref', 'set', unicode, multi=True)
        self.sets.append(self.content_type)
        self.sets.extend(self.xpath('ex:scope/text()', 'scope', unicode, multi=True))
        self.is_set = self.content_type == 'set'

        if self.content_type == 'person':
            self._fields = self.set_person_fields()
        else:
            self._fields = self.set_publication_fields()

    def set_publication_fields(self):
        fields = {
            'description': [
            self.xpath('ex:abstract/text()', 'abstract', unicode)],
            'title': [self.label],
            'date': self.xpath('ex:issued/text()', 'subject', datetime, multi=True),
            'subject': self.xpath('ex:keyword/text()', 'subject', unicode, multi=True),
            'identifier': ['http://purl.example.org/%s' % self.id],
            'language': self.xpath('ex:abstract/@xml:lang', 'author', unicode, multi=True),
            'type': [self.content_type]
        }
        
        if 'public' in self.sets:
           fields['rights'] = ['public domain, no restrictions']

        authors = []
        author_rel = []
        ids = self.xpath('ex:author/@ref', 'author', unicode, multi=True)
        for id in ids:
            author_rel.append(id)
            person = ExampleContentObject()
            person.update(
                self.provider.get_content_by_id(id.replace(':','_')+'.xml'),
                self.provider)
            authors.append(person.label)
        fields['author'] = authors
        fields['author_rel'] = author_rel
        fields['contributor'] = authors
        fields['url'] = ['http://hdl.handle.net/????/%s' % self.id]
        fields['dare_id'] = ['urn:NBN:nl:ui:??-%s' %self.id]

        assets = []
        for el in self.root.xpath('ex:asset', namespaces=self.nsmap):
            asset = {}
            for child in el.xpath('*[text()]'):
                asset[child.tag.split('}')[-1]] = child.text
            assert 'filename' in asset, 'found asset without filename'
            assert 'mimetype' in asset, 'found asset without mimetype'
            asset['url'] = 'http://example.org/repo/assets/%s/%s' % (self.id.replace(':', '_'),
                                                                     asset['filename'])
            assets.append(asset)
        fields['asset'] = assets
        
        return fields

    def set_person_fields(self):
        fields = {
            'name' : [self.label],
            'surname': self.xpath('ex:surname/text()', 'surname', unicode, multi=True),
            'firstname': self.xpath('ex:firstname/text()', 'firstname', unicode, multi=True),
            'initials': self.xpath('ex:initials/text()', 'initials', unicode, multi=True),
            'dai': self.xpath('ex:dai/text()', 'initials', unicode, multi=True),
            }
        return fields
