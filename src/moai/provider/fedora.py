import os
import urllib2
import md5

from zope.interface import implements

from moai.provider.oai import OAIBasedContentProvider
from moai.interfaces import IContentProvider

class FedoraBasedContentProvider(OAIBasedContentProvider):
    """Providers content by harvesting a Fedora Commons OAI feed.
    Then uses the content from a specific datastream, or retrieves the
    full foxml file if no datastream is provided
    Implements the :ref:`IContentProvider` interface
    """
    
    implements(IContentProvider)
    
    
    def __init__(self, fedora_url, output_path,
                 datastream_name=None, username=None, password=None):
        oai_url = '%s/oai' % fedora_url
        super(FedoraBasedContentProvider, self).__init__(oai_url, output_path)
        self._stream = datastream_name
        self._fedora_url = fedora_url
        self._user = username
        self._pass = password
        if not os.path.isdir(output_path):
            os.mkdir(output_path)

    def _get_id(self, header):
        fedora_id = ':'.join(header.identifier().split(':')[2:])
        return fedora_id

    def _process_record(self, header, element):

        fedora_id = self._get_id(header)
        
        if self._stream is None:
            url = '%s/objects/%s/objectXML' % (self._fedora_url,
                                               fedora_id)
        else:
            # get only a specific data stream
            url = '%s/get/%s/%s' % (self._fedora_url,
                                    fedora_id, 
                                    self._stream)

        if self._user and self._pass:
            password = ('%s:%s' % (self._user, self._pass)).strip().encode('base64')
            headers = {'Authorization': 'Basic %s' % password}
            request = urllib2.Request(url, headers=headers)
        else:
            request = urllib2.Request(url)

        try:
            fp = urllib2.urlopen(request)
            xml_data = fp.read()
            fp.close()
        except urllib2.HTTPError, err:
            self._log.warning('HTTP %s -> Can not get Fedora data: %s' % (err.code, url))
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
