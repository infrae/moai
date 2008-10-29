import datetime

from zope.interface import implements

from moai.interfaces import IContentProvider
from moai.content import DictBasedContentObject, DictBasedContentSet

class ListBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, content, sets):
        self._content = content
        self._sets = sets

    def update(self, from_date):
        return []

    def count(self):
        return len(self._content)

    def get_content(self):
        return [DictBasedContentObject(c.copy(), self) for c in self._content]

    def get_content_by_id(self, id):
        result = [d for d in self._content if d['id'] == id]
        if result:
            return DictBasedContentObject(result[0].copy(), self)

    def get_sets(self):
        return [DictBasedContentSet(s.copy(), self) for s in self._sets]

    def get_set_by_id(self, id):
        result = [s for s in self._sets if s['id'] == id]
        if result:
            return DictBasedContentSet(result[0].copy(), self)
