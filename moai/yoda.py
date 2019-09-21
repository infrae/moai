from lxml import etree
from datetime import datetime, timedelta

from moai.utils import XPath, get_moai_log

import json


class YodaContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.sets = {}
        self.deleted = False
        self.metadata = dict()

    def update(self, path):
        log = get_moai_log()

        log.warning(path)


 
        with open(path, 'r') as myfile:
            jsonSchemaData = myfile.read()

        log = get_moai_log()
        log.warning(jsonSchemaData)

        dictJsonData = json.loads(jsonSchemaData)

	# Modified and id are required for the system to operate
        
        # dictJsonData['System']['Last_Modified_Date']
        persistent_identifier_datapackage = dictJsonData['System']['Persistent_Identifier_Datapackage']['Identifier']

	self.id = 'oai:%s' % persistent_identifier_datapackage   #i.decode('unicode-escape')
        self.modified = datetime.now() - timedelta(days=1)

        self.metadata['identifier'] = [persistent_identifier_datapackage]

        self.metadata['metadata'] = dictJsonData  
