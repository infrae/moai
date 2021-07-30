import json
from datetime import datetime, timedelta

from moai.utils import get_moai_log


class YodaContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.sets = {}
        self.deleted = False
        self.metadata = dict()

    def update(self, path):
        try:
            with open(path, 'r') as myfile:
                jsonSchemaData = myfile.read()

            dictJsonData = json.loads(jsonSchemaData)
        except Exception:
            log = get_moai_log()
            log.warning("Could not load JSON metadata file: {}".format(path))
            return False

            # Modified and id are required for the system to operate
        persistent_identifier_datapackage = dictJsonData['System']['Persistent_Identifier_Datapackage']['Identifier']

        self.id = 'oai:%s' % persistent_identifier_datapackage  # i.decode('unicode-escape')
        self.modified = datetime.now() - timedelta(days=1)
        self.metadata['identifier'] = [persistent_identifier_datapackage]
        self.metadata['metadata'] = dictJsonData
