import os
import sys
import datetime
import fnmatch

from zope.interface import implements

from moai.interfaces import IContentProvider
from moai.content import DictBasedContentObject
from moai.error import ContentError

class FileBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, path, content_filter="*"):
        self._path = path
        self._filter = content_filter
        self._files = self._build_filelist()

    def set_logger(self, log):
        self._log = log
        
    def _build_filelist(self, from_time=None):
        result = []
        for p, d, f in os.walk(self._path):
            for directory in d:
                if directory.startswith('.'):
                    d.remove(directory)
            for file in f:
                if file[0] in ['.', '#']:
                    continue
                if not fnmatch.fnmatch(file, self._filter):
                    continue
                path = os.path.join(p, file)
                if not from_time is None:
                    mtime= os.path.getmtime(path)
                    if mtime < from_time:
                        continue
                result.append(path)
        return result

    def update(self, from_date):
        from_time = time.mktime(datetime.timetuple())
        result = []
        for path in self._build_filelist(from_time=from_time):
            result.append(path)
            if path not in self._files:
                self._files.append(path)
        return result

    def count(self):
        return len(self._files)

    def set_content_class(self, content_object_class):
        self._content_object_class = content_object_class
        
    def get_content(self):
        for path in self._files:
            obj = self._content_object_class()
            try:
                obj.add_data(path)
            except Exception:
                yield ContentError(self._content_object_class, path)
                continue
            yield obj
