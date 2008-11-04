import os
import urllib2

from moai.provider.oai import OAIBasedContentProvider

class FedoraBasedContentProvider(OAIBasedContentProvider):
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
        
        path = os.path.join(self._path, '%s.xml' % fedora_id)
        fp = open(path, 'w')
        fp.write(xml_data)
        fp.close()
        return True
