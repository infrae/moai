from lxml import etree
from datetime import datetime, timedelta

from moai.utils import XPath, get_moai_log


class YodaContent(object):
    def __init__(self, provider):
        self.provider = provider
        self.id = None
        self.modified = None
        self.deleted = False
        self.sets = dict()
        self.metadata = dict()

    def update(self, path):
        log = get_moai_log()
        try:
            doc = etree.parse(path)
	except etree.ParseError:
            log.warning("Failed to parse %s".format(path))
            return

        xpath = XPath(doc, nsmap={})

        self.root = doc.getroot()
	
        id = xpath.string('//Persistent_Identifier_Datapackage')
	if not id:
            log.warning("Missing Persistent Identifier of Datapackage in %s".format(path))
            return
	
        self.id = 'oai:%s' % id

        self.metadata['identifier'] = [id]

	last_modified = xpath.string('//Last_Modified_Date')
        if not last_modified:
            log.warning("Missing Last Modified Time in %s".format(path))
            self.modified = datetime.now() - timedelta(days=1)
        else:
            self.modified = datetime.strptime(last_modified, "%Y-%M-%d")

        author_data = []
        creators = xpath.strings('//Creator/Name')
        if creators:
            self.metadata['creator'] = creators
            for creator in creators:
                author_data.append({u"name": creator, u"role": [u"auth"]})

	contributors = xpath.strings('//Contributor/Name')
        if contributors:
            self.metadata['contributor'] = contributors
            for contributor in contributors:
                author_data.append({u"name": contributor, u"role": [u"cont"]})
	
	self.metadata["author_data"]= author_data

        title = xpath.string('//Title')
        if title:
            self.metadata['title'] = [title]

        description = xpath.string('//Description')
        if description:
            self.metadata['description'] = [description]

        language = xpath.string('//Language')
        if language:
            self.metadata['language'] = [language]
	
	datesinxml = [xpath.string('//Publication_Date'),
                      xpath.string('//Embargo_End_Date')]

        dates = [d for d in datesinxml if d]
        if dates:
            self.metadata['date'] = dates

        rightsinxml = [xpath.string('//License'),
                       xpath.string('//License/Properties/URL')]

        rights = [r for r in rightsinxml if r]
        if rights:
            self.metadata['rights'] = rights

        subjectinxml = xpath.strings('//Discipline') + xpath.strings('//Tag')
        subject = [s for s in subjectinxml if s]
        if subject:
           self.metadata['subject'] = subject
       
        locations = xpath.strings('//Location_Covered')
        perioddates = [xpath.string('//Start_Period'), xpath.string('//End_Period')]
        period = "/".join([d for d in perioddates if d])
        if period:
            coverage = locations + [period]
        else:
            coverage = locations
        if coverage:
            self.metadata['coverage'] = coverage

	relations = xpath.strings('//Persistent_Identifier')
        if relations:
            self.metadata['relation'] = relations

	self.sets[u'yoda'] = {
            u'name': u'YoDa',
            u'description': u'share-collaborate environment for research data'
        }
