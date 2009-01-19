import os
import urllib2
import md5

from zope.interface import implements

from moai.provider.oai import OAIBasedContentProvider
from moai.interfaces import IContentProvider

class FedoraBasedContentProvider(OAIBasedContentProvider):
    """Providers content by harvesting a Fedora Commons OAI feed.
    Then uses the content from a specific datastream
    Implements the :ref:`IContentProvider` interface
    """
    
    implements(IContentProvider)
    
    
    def __init__(self, fedora_url, output_path, datastream_name):
        oai_url = '%s/oai' % fedora_url
        super(FedoraBasedContentProvider, self).__init__(oai_url, output_path)
        self._stream = datastream_name
        self._fedora_url = fedora_url
        if not os.path.isdir(output_path):
            os.mkdir(output_path)

    def _get_id(self, header):
        fedora_id = ':'.join(header.identifier().split(':')[2:])
        return fedora_id

    def _process_record(self, header, element):

        fedora_id = self._get_id(header)
        
        url = '%s/get/%s/%s' % (self._fedora_url,
                                fedora_id,
                                self._stream)

        try:
            fp = urllib2.urlopen(url)
            xml_data = fp.read()
            fp.close()
        except urllib2.HTTPError, err:
            self._log.warning('Can not get Fedora datastream: %s' % url)
            return False

        directory = md5.new(fedora_id).hexdigest()[:3]

        path = os.path.join(self._path, directory)
        if not os.path.isdir(path):
            os.mkdir(path)
                
        path = os.path.join(path, '%s.xml' % fedora_id)
        
        fp = open(path, 'w')
        fp.write(xml_data)
        fp.close()
        return True
