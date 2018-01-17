from lxml import etree
from datetime import datetime, timedelta

from moai.utils import XPath, get_moai_log


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
        try:
            doc = etree.parse(path)
	except etree.ParseError:
            log.warning("Failed to parse %s".format(path))
            return

        xpath = XPath(doc, nsmap={})

        self.root = doc.getroot()

        id = xpath.string("/metadata/System/Persistent_Identifier_Datapackage[Identifier_Scheme='DOI']/Identifier")
	if not id:
            log.warning("Missing Persistent Identifier (DOI) of Datapackage in %s".format(path))
            return

        self.id = 'oai:%s' % id

        self.metadata['identifier'] = [id]

	last_modified = xpath.string('//Last_Modified_Date')
        if not last_modified:
            log.warning("Missing Last Modified Time in %s".format(path))
            self.modified = datetime.now() - timedelta(days=1)
        else:
            ret = datetime.strptime(last_modified[0:19],'%Y-%m-%dT%H:%M:%S')
    	    if last_modified[19]=='+':
                ret-=timedelta(hours=int(last_modified[20:22]),minutes=int(last_modified[22:]))
            elif last_modified[19]=='-':
                ret+=timedelta(hours=int(last_modified[20:22]),minutes=int(last_modified[22:]))
            self.modified = ret

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
                       xpath.string('//System/License_URL')]

        rights = [r for r in rightsinxml if r]
        if rights:
            self.metadata['rights'] = rights

        subjectinxml = xpath.strings('//Discipline') + xpath.strings('//Tag')
        subject = [s for s in subjectinxml if s]
        if subject:
           self.metadata['subject'] = subject

        locations = xpath.strings('//Covered_Geolocation_Place')

        geoLocation = xpath.strings('//geoLocation')
        westBoundLongitude = xpath.strings('//geoLocation/westBoundLongitude')
        eastBoundLongitude = xpath.strings('//geoLocation/eastBoundLongitude')
        southBoundLatitude = xpath.strings('//geoLocation/southBoundLatitude')
        northBoundLatitude = xpath.strings('//geoLocation/northBoundLatitude')
        coordinates = ",".join([westBoundLongitude,southBoundLatitude,eastBoundLongitude,northBoundLatitude])

        perioddates = [xpath.string('//Covered_Period/Start_Date'), xpath.string('//Covered_Period/End_Date')]
        period = "/".join([d for d in perioddates if d])

        if period and geoLocation:
            coverage = locations + [period] + coordinates
        if geoLocation:
            coverage = locations + coordinates
        if period:
            coverage = locations + [period]
        else:
            coverage = locations
        if coverage:
            self.metadata['coverage'] = coverage
