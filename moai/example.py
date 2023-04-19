
from lxml import etree

from moai.utils import XPath


class ExampleContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.deleted = None
        self.sets = None
        self.metadata = None

    def update(self, path):
        doc = etree.parse(path)
        xpath = XPath(doc, nsmap={'x': 'http://example.org/data'})

        self.root = doc.getroot()

        id = xpath.string('//x:id')
        self.id = 'oai:example-%s' % id
        self.modified = xpath.date('//x:modified')
        self.deleted = False

        author_data = []
        for num, _el in enumerate(xpath('//x:author'), 1):
            first = xpath.string('//x:author[%d]/x:givenName' % num)
            sur = xpath.string('//x:author[%d]/x:familyName' % num)
            name = '%s %s' % (first, sur)
            author_data.append({'name': [name],
                                'surname': [sur],
                                'firstname': [first],
                                'role': ['aut']})

        self.metadata = {'identifier': ['http://example.org/data/%s' % id],
                         'title': [xpath.string('//x:title')],
                         'subject': xpath.strings('//x:subject'),
                         'description': [xpath.string('//x:abstract')],
                         'creator': [d['name'][0] for d in author_data],
                         'author_data': author_data,
                         'language': ['en'],
                         'date': [xpath.string('//x:issued')]}

        self.sets = {'example': {'name': 'example',
                                 'description': 'An Example Set'}}

        access = xpath.string('//x:access')
        if access == 'public':
            self.sets['public'] = {'name': 'public',
                                   'description': 'Public access'}
            self.metadata['rights'] = ['open access']
        elif access == 'private':
            self.sets['private'] = {'name': 'private',
                                    'description': 'Private access'}
            self.metadata['rights'] = ['restricted access']
