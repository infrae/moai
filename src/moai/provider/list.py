import datetime

from zope.interface import implements

from moai.interfaces import IContentProvider
from moai.content import DictBasedContentObject
from moai.error import ContentError

class ListBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, content):
        self._content = content

    def set_logger(self, log):
        self._log = log

    def update(self, from_date=None):
        return self.get_content_ids()

    def count(self):
        return len(self._content)

    def get_content_ids(self):
        return range(len(self._content))

    def get_content_by_id(self, id):
        return self._content[id]



