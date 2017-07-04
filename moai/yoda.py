from lxml import etree
from datetime import datetime, timedelta

from moai.utils import XPath


class YodaContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.deleted = None
        self.sets = None
        self.metadata = None

    def update(self, path):
        doc = etree.parse(path)
        xpath = XPath(doc, nsmap={})

        self.root = doc.getroot()

        id = xpath.string('//Project_ID')
        self.id = 'oai:%s' % id
        self.modified = datetime.now() - timedelta(days=1)
        self.deleted = True

        author_data = []

        # Add creator of dataset.
        author_data.append({'name': [xpath.string('//Creator')],
                            'role': [u'aut']})

        # Add all contributors to dataset.
        for num, el in enumerate(xpath('//Contributor'), 1):
            contributor = [xpath.string('//Contributor[%d]' % num)]
            author_data.append({'name': contributor,
                                 'role': [u'aut']})

        # Add metadata of dataset.
        self.metadata = {'identifier': [id],
                         'title': [xpath.string('//Project_Title')],
                         'subject': [xpath.string('//Project_Description')],
                         'description': [xpath.string('//Project_Description')],
                         'creator': [d['name'][0] for d in author_data],
                         'author_data': author_data,
                         'language': [xpath.string('//Language_dataset')],
                         'date': [xpath.string('//Embargo')]}

       	# Clean dataset type.
        type = xpath.string('//Dataset_Type')
        type = type.replace(" ", "_")

        # Specify dataset.
        self.sets = {type:
                     {u'name':xpath.string('//Dataset_Title'),
                      u'description':xpath.string('//Dataset_Description')}}

        published = xpath.string('//Publish_Metadata')
        if published == 'Yes':
            self.deleted = False      
