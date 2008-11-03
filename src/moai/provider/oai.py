import os
import datetime

from zope.interface import implements
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry
from lxml import etree

from moai.interfaces import IContentProvider
from moai.content import DictBasedContentObject
from moai.error import ContentError

class OAIBasedContentProvider(object):
    implements(IContentProvider)

    def __init__(self, oai_url, output_path, metadata_prefix='oai_dc'):
        self.url = oai_url
        self.path = output_path
        self.prefix = metadata_prefix
        self._content = {}

    def set_logger(self, log):
        self._log = log

    def update(self, from_date=None):
        self._log.info('Harvesting oai server: %s' % self.url)
        registry = MetadataRegistry()
        registry.registerReader(self.prefix, lambda el: el)

        client = Client(self.url, registry)
        for header, element, about in client.listRecords(
            metadataPrefix = self.prefix,
            from_ = from_date):
            added = self._process_record(header, element)
            if added:
                yield self._get_id(header)

    def _get_id(self, header):
        return header.identifier()

    def _process_record(self, header, element):

        oai_id = self._get_id(header)
        path = os.path.join(self.path, '%s.xml' % oai_id)
        fp = open(path, 'w')
        fp.write(etree.tostring(element, encoding="utf8"))
        fp.close()
        self._content[oai_id] = path
        return True

    def count(self):
        return len(self._content)

    def get_content_ids(self):
        return range(len(self._content))

    def get_content_by_id(self, id):
        return self._content[id]
