import datetime

from zope.interface import implements

from moai.interfaces import IContentProvider
from moai.content import DictBasedContentObject
from moai.error import ContentError

class ListBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, content):
        self._content = content
        self._content_object_class = None

    def set_logger(self, log):
        self._log = log

    def update(self, from_date):
        return []

    def count(self):
        return len(self._content)

    def set_content_class(self, content_object_class):
        self._content_object_class = content_object_class
        
    def get_content(self):
        for id, content in enumerate(self._content):
            obj = self._content_object_class()
            try:
                obj.update(content, self)
            except Exception, err:
                yield ContentError(self._content_object_class, id)
                continue
            yield obj

    def get_content_by_id(self, id):
        obj = self._content_object_class()
        obj.update(self._content[id], self)
        return obj



