import os

from zope.interface import implements
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry
from oaipmh.error import NoRecordsMatchError
from lxml import etree

from moai.interfaces import IContentProvider
from moai.provider.file import FileBasedContentProvider

class OAIBasedContentProvider(FileBasedContentProvider):
    """Providers content by harvesting OAI feeds.
    Implements the :ref:`IContentProvider` interface
    """
    
    implements(IContentProvider)

    def __init__(self, oai_url, output_path, metadata_prefix='oai_dc'):
        super(OAIBasedContentProvider, self).__init__(output_path, '*.xml')
        self._url = oai_url
        self._prefix = metadata_prefix

    def set_logger(self, log):
        self._log = log

    def update(self, from_date=None):
        self._log.info('Harvesting oai server: %s' % self._url)
        registry = MetadataRegistry()
        registry.registerReader(self._prefix, lambda el: el)

        client = Client(self._url, registry)
        try:
            for header, element, about in client.listRecords(
                metadataPrefix = self._prefix,
                from_ = from_date):
                added = self._process_record(header, element)
                if added:
                    yield self._get_id(header)
        except NoRecordsMatchError:
            pass

        super(OAIBasedContentProvider, self).update()

    def _get_id(self, header):
        return header.identifier()

    def _process_record(self, header, element):

        oai_id = self._get_id(header)
        path = os.path.join(self.path, '%s.xml' % oai_id)
        fp = open(path, 'w')
        fp.write(etree.tostring(element, encoding="utf8"))
        fp.close()
        return True

