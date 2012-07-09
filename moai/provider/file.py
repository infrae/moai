import os
import time
import fnmatch


class FileBasedContentProvider(object):
    """Provides content by reading directories of files
    Implements the :ref:`IContentProvider` interface
    """
    def __init__(self, uri, content_filter="*"):
        assert uri.startswith('file://'), 'unknown uri format'
        path = uri[7:]
        basedir, filename = os.path.split(path)
        if '*' in filename or '?' in filename:
            content_filter = filename
            self._path = basedir
        else:
            self._path = path
        self._filter = content_filter
        self._content = {}

    def set_logger(self, log):
        self._log = log
        
    def _harvest(self, from_time=None):
        result = {}
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
                id = os.path.basename(path)
                result[id] = path
        return result

    def update(self, from_date=None):
        if from_date is None:
            from_time = None
        else:
            from_time = time.mktime(from_date.timetuple())
        result = self._harvest(from_time=from_time)
        self._content.update(result)
        return result.keys()

    def count(self):
        return len(self._content)

    def get_content_ids(self):
        for id in self._content.keys():
            yield id

    def get_content_by_id(self, id):
        return self._content[id]
