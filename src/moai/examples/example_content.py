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
        self.content_type = unicode(self.root.xpath('local-name()'))
        if self.content_type == 'publication':
            self.label = self.xpath('ex:title/text()', 'label', unicode, required=True)
        else:
            self.label = self.xpath('ex:name/text()', 'label', unicode, required=True)
            
        self.when_modified = datetime(*time.gmtime(os.path.getmtime(path))[:6])
        self.deleted = False
        self.sets = self.xpath('ex:set/@ref', 'set', unicode, multi=True)
        self.sets.append(self.content_type)
        self.sets.extend(self.xpath('ex:scope/text()', 'scope', unicode, multi=True))
        self.is_set = self.content_type == u'set'

        self._assets = []
        if self.content_type == u'person':
            self._fields = self.set_person_fields()
        elif self.content_type == u'set':
            self._fields = self.set_set_fields()
        else:
            self._fields = self.set_publication_fields()

        # Instead of letting the updater fail the record on not-valid XML,
        # remove the conflicting characters 
        #self._sanitize()

    def set_set_fields(self):
        return {u'name': [self.label],
                u'description': self.xpath(
            'ex:description/text()',
            'description',
            unicode,
            multi=True)}
        
    def set_publication_fields(self):
        fields = {
            u'description': [
            self.xpath('ex:abstract/text()', 'abstract', unicode)],
            u'title': [self.label],
            u'date': self.xpath('ex:issued/text()',
                                'subject', datetime, multi=True),
            u'subject': self.xpath('ex:keyword/text()',
                                   'subject', unicode, multi=True),
            u'identifier': ['http://purl.example.org/%s' % self.id],
            u'language': self.xpath('ex:abstract/@xml:lang',
                                    'author', unicode, multi=True),
            u'type': [self.content_type]
        }

        if fields['date']:
            # fields should always be unicode
            fields['date'] = [unicode(fields['date'][0].isoformat())]
        
        if 'public' in self.sets:
           fields[u'rights'] = [u'public domain, no restrictions']

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
        fields[u'author'] = authors
        fields[u'author_rel'] = author_rel
        fields[u'contributor'] = authors
        fields[u'url'] = [u'http://hdl.handle.net/????/%s' % self.id]
        fields[u'dare_id'] = [u'urn:NBN:nl:ui:??-%s' %self.id]

        for el in self.root.xpath('ex:asset', namespaces=self.nsmap):
            asset = {}
            for child in el.xpath('*[text()]'):
                asset[child.tag.split('}')[-1]] = unicode(child.text)
            assert u'filename' in asset, 'found asset without filename'
            assert u'mimetype' in asset, 'found asset without mimetype'
            asset[u'url'] = u'asset/%s/%s' % (
                self.id,
                asset['filename'])
            
            path = os.path.join(os.path.dirname(__file__),
                                'example_data',
                                'assets', self.id,
                                asset['filename'])
            assert os.path.isfile(path), "Can not find asset: %s" % path

            asset[u'absolute_uri'] = u'file://%s' % path
            asset[u'md5'] = u''
            asset[u'metadata'] = {}
            if asset[u'access']:
                asset[u'metadata'][u'access'] = [asset[u'access']]
                del asset[u'access']
            if asset[u'modified']:
                asset[u'metadata'][u'modified'] = [asset[u'modified']]
                del asset[u'modified']
            self._assets.append(asset)
                
        #fields[u'asset'] = assets
        
        return fields

    def get_assets(self):
        return self._assets

    def set_person_fields(self):
        fields = {
            u'name' : [self.label],
            u'surname': self.xpath('ex:surname/text()',
                                   'surname', unicode, multi=True),
            u'firstname': self.xpath('ex:firstname/text()',
                                     'firstname', unicode, multi=True),
            u'initials': self.xpath('ex:initials/text()',
                                    'initials', unicode, multi=True),
            u'dai': self.xpath('ex:dai/text()',
                               'initials', unicode, multi=True),
            }
        return fields
