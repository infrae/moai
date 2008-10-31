import time
import datetime

from zope.interface import implements
from lxml import etree

from moai.interfaces import IContentObject

class DictBasedContentObject(object):
    implements(IContentObject)

    def update(self, data, provider):
        self.provider = provider
        data = data.copy()
        self.id = self.extract_id(data)
        self.label = self.extract_label(data)
        self.content_type = self.extract_content_type(data)
        self.when_modified = self.extract_when_modified(data)
        self.deleted = self.extract_deleted(data)
        self.sets = self.extract_sets(data)
        self.is_set = self.extract_is_set(data)
        self._fields = self.extract_fields(data)
        
    def extract_id(self, data):
        id = data.pop('id')
        assert (isinstance(id, unicode), 'id should be a unicode value')
        return id

    def extract_label(self, data):
        label = data.pop('label')
        assert (isinstance(label, unicode), 'label should be a unicode value')
        return label

    def extract_content_type(self, data):
        content_type = data.pop('content_type')
        assert (isinstance(content_type, unicode),
                          'content_type should be a unicode value')
        return content_type

    def extract_when_modified(self, data):
        when_modified = data.pop('when_modified')
        assert (isinstance(when_modified, datetime.datetime),
                'when_modified should be a datetime object')
        return when_modified

    def extract_deleted(self, data):        
        deleted = data.pop('deleted')
        assert (isinstance(deleted, bool),
                 'when_modified should be a datetime object')
        return deleted

    def extract_sets(self, data):
        sets = data.pop('sets')
        assert (isinstance(sets, list),
                'sets should be a list object')
        return sets

    def extract_is_set(self, data):
        is_set = data.pop('is_set')
        assert (isinstance(is_set, bool), 'is_set should be a boolean')
        return is_set

    def extract_fields(self, data):
        return data

    def field_names(self):
        return self._fields.keys()

    def get_values(self, field_name):
        result = self._fields.get(field_name, [])
        assert isinstance(result, list)
        return result



class XMLContentObject(object):
    implements(IContentObject)
    
    def xpath(self, xpath, name, pytype, required=False, multi=False):
        values = self.root.xpath(xpath, namespaces=self.nsmap)
        if required:
            assert values, 'required value "%s" is missing' % name
        
        result = []

        for value in values:
            assert isinstance(value, basestring), (
                'xpath result of value "%s" is of type "%s", expected string|unicode' %(
                name, type(value).__name__))

            if pytype is datetime.datetime:
                value = datetime.datetime(*time.strptime(value, '%Y-%m-%dT%H:%M:%S')[:6])
            try:
                if type(value) != pytype:
                    pyval = pytype(value)
            except:
                raise ValueError('can not convert %s value "%s" into %s' % (name, value, pytype))
            result.append(value)

            
        if not multi and result:
            result = result[0]
        return result

    def update(self, path, provider):
        self.provider = provider
        self.nsmap = {}
        doc = etree.parse(path)
        self.root = doc.getroot()
        
        self.id = self.extract_id(root)
        self.label = self.extract_label(root)
        self.content_type = self.extract_content_type(root)
        self.when_modified = self.extract_when_modified(root)
        self.deleted = self.extract_deleted(root)
        self.sets = self.extract_sets(root)
        self.is_set = self.extract_is_set(root)
        self._fields = self.extract_fields(root)

    def  extract_id(self, root):
        id = root.xpath('id/text()')
        assert id, 'id field is missing'
        id = unicode(id[0])
        assert (isinstance(id, unicode), 'id should be a unicode value')
        return id

    def extract_label(self, root):
        label = unicode(root.xpath('label/text()'))
        assert label, 'label field is missing'
        label = unicode(label[0])
        assert (isinstance(label, unicode), 'label should be a unicode value')
        return label

    def extract_content_type(self, root):
        content_type = unicode(root.xpath('content_type/text()')[0])
        assert (isinstance(content_type, unicode),
                          'content_type should be a unicode value')
        return content_type

    def extract_when_modified(self, root):
        when_modified = unicode(root.xpath('when_modified')[0])
        when_modified = datetime.datetime(*time.strptime(when_modified,
                                                         '%Y-%m-%dT%H:%M:%S')[:6])
        assert (isinstance(when_modified, datetime.datetime),
                'when_modified should be a datetime object')
        return when_modified

    def extract_deleted(self, root):        
        deleted = unicode(root.xpath('deleted/text()')[0]).lower == 'true'
        assert (isinstance(deleted, bool),
                 'when_modified should be a datetime object')
        return deleted

    def extract_sets(self, root):
        sets = [unicode(s) for s in root.xpath('set')]
        assert (isinstance(sets, list),
                'sets should be a list object')
        return sets

    def extract_is_set(self, root):
        is_set = unicode(root.xpath('is_set/text()')[0]).lower == 'true'
        assert (isinstance(is_set, bool), 'is_set should be a boolean')
        return is_set

    def extract_fields(self, root):
        result = {}
        for node in root.xpath('*[text(.)]'):
            tagname = node.tag.split('}')[-1]
            if tagname in ['is_set', 'set', 'deleted', 'when_modified',
                           'content_type', 'label', 'id']:
                continue
            result.setdefault(tagname, []).append(node.text)

    def field_names(self):
        return self._fields.keys()

    def get_values(self, field_name):
        result = self._fields.get(field_name, [])
        assert isinstance(result, list), 'value of "%s" is not a list' % field_name
        return result

