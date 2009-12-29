import time

from zope.interface import implements

from moai.interfaces import IContentProvider

class ListBasedContentProvider(object):
    """Provides content from a python list,
    implementation of :ref:`IContentProvider`"""
    
    implements(IContentProvider)

    def __init__(self, content):
        self._content = content

    def set_logger(self, log):
        self._log = log

    def update(self, from_date=None):
        return self.get_content_ids(from_date)

    def count(self):
        return len(self._content)

    def get_content_ids(self, from_date=None):
        if from_date is None:
            return range(len(self._content))
        else:
            from_time = time.mktime(from_date.timetuple())

            result = []
            for id in range(len(self._content)):
                when_mod = self.get_content_by_id(id).get('when_modified', '')

                if when_mod != '':
                    when_mod = time.mktime(when_mod.timetuple())
                
                    if from_time <= when_mod:
                        result.append(id)

            return result

    def get_content_by_id(self, id):
        return self._content[id]



