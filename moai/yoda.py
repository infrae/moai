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
            log.warning("Missing Persistent Identifier (DOI) of Datapackage in " + path)
            return

        self.id = 'oai:%s' % id

        self.metadata['identifier'] = [id]

        last_modified = xpath.string('//Last_Modified_Date')

        if not last_modified:
            log.warning("Missing Last Modified Time in %s".format(path))
            self.modified = datetime.now() - timedelta(days=1)
        else:
            ret = datetime.strptime(last_modified[0:19],'%Y-%m-%dT%H:%M:%S')
            if len(last_modified)>19:
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

        # Funding references
        fundingRefs = []
        funders = xpath('//Funding_Reference')

        if len(funders):
            for funder in funders:
                funderDict = {}

                if funder.find('Funder_Name') is not None:
                    funderDict["name"] = funder.find('Funder_Name').text
                if funder.find('Properties/Award_Number') is not None:
                    funderDict["awardNumber"] = funder.find('Properties/Award_Number').text
                fundingRefs.append(funderDict)
            self.metadata["fundingReferences"] = fundingRefs

        # Related datapackages i.e. related identifiers
        relatedIdentifiers = []
        packages = xpath('//Related_Datapackage')

        if len(packages):
            for package in packages:
                relatedDict = {}
                if package.find('Properties/Title') is not None:
                    relatedDict["title"] = package.find('Properties/Title').text
                if package.find('Properties/Persistent_Identifier/Identifier_Scheme') is not None:
                    relatedDict["relatedIdentifierScheme"] = package.find('Properties/Persistent_Identifier/Identifier_Scheme').text
                if package.find('Properties/Persistent_Identifier/Identifier') is not None:
                    relatedDict["relatedIdentifier"] = package.find('Properties/Persistent_Identifier/Identifier').text

                if package.find('Relation_Type') is not None:
                    relatedDict["relationType"] = package.find('Relation_Type').text

                relatedIdentifiers.append(relatedDict)

            self.metadata["relatedIdentifiers"] = relatedIdentifiers

        # Contributors datacite - yoda contributor can hold n idf/idf_schemes. Does datacite?
        dataciteContributors = []
        dcContributors = xpath('//Contributor')

        if len(dcContributors):
            for contrib in dcContributors:
                contribDict = {}
                if contrib.find('Name') is not None:
                    contribDict["name"] = contrib.find('Name').text
                if contrib.find('Properties/Affiliation') is not None:
                     contribDict['affiliation'] =  contrib.find('Properties/Affiliation').text

                if contrib.find('Properties/Contributor_Type') is not None:
                    contribDict["type"] = contrib.find('Properties/Contributor_Type').text
                if contrib.find('Properties/Person_Identifier/Name_Identifier') is not None:
                    contribDict["name_identifier"] = contrib.find('Properties/Person_Identifier/Name_Identifier').text
                if contrib.find('Properties/Person_Identifier/Name_Identifier_Scheme') is not None:
                    contribDict["name_identifier_scheme"] = contrib.find('Properties/Person_Identifier/Name_Identifier_Scheme').text

                dataciteContributors.append(contribDict)

            self.metadata['dataciteContributors'] = dataciteContributors


        # Creators datacite - yoda creators can hold n idf/idf_schemes. Does datacite?
        dataciteCreators = []
        dcCreators = xpath('//Creator')

        if len(dcCreators):
            for creator in dcCreators:
                creatorDict = {}
                if creator.find('Name') is not None:
                    creatorDict['name'] =  creator.find('Name').text

                if creator.find('Properties/Affiliation') is not None:
                     creatorDict['affiliation'] =  creator.find('Properties/Affiliation').text

                if creator.find('Properties/Person_Identifier/Name_Identifier') is not None:
                     creatorDict['name_identifier'] = creator.find('Properties/Person_Identifier/Name_Identifier').text

                if creator.find('Properties/Person_Identifier/Name_Identifier_Scheme') is not None:
                     creatorDict['name_identifier_scheme'] = creator.find('Properties/Person_Identifier/Name_Identifier_Scheme').text

                dataciteCreators.append(creatorDict)

            self.metadata['dataciteCreators'] = dataciteCreators

        title = xpath.string('//Title')
        if title:
            self.metadata['title'] = [title]

        description = xpath.string('//Description')
        if description:
            self.metadata['description'] = [description]

        language = xpath.string('//Language')
        if language:
            self.metadata['language'] = [language[0:2]]
        else:
            self.metadata['language'] = ['en']

        version = xpath.string('//Version')
        if version:
            self.metadata['version'] = version

        # Dates - handling dublin core
        datesinxml = [xpath.string('//Publication_Date'),
                      xpath.string('//Embargo_End_Date')]

        dates = [d for d in datesinxml if d]
        if dates:
            self.metadata['date'] = dates

        # Dates - handling datacite
        dataciteDates = {}
        if xpath.string('//System/Last_Modified_Date'):
            dataciteDates['updated'] = xpath.string('//System/Last_Modified_Date')[0:10]
        if xpath.string('//Embargo_End_Date'):
            dataciteDates['available'] = xpath.string('//Embargo_End_Date')[0:10]

        # embargo is handled differently in test schema - old school flex date
        embargo = xpath('//Embargo_End_Date')
        #if embargo.find('Embargo_End_Date_YYYY_MM_DD') is not None:
        #    embargoEndDate = embargo.find('Embargo_End_Date_YYYY_MM_DD').text
        #elif embargo.find('Embargo_End_Date_YYYY_MM') is not None:
        #    embargoEndDate = embargo.find('Embargo_End_Date_YYYY_MM').text
        #elif embargo.find('Embargo_End_Date_YYYY') is not None:
        #    embargoEndDate = embargo.find('Embargo_End_Date_YYYY').text
        #else:
        #    embargoEndDate = embargo.text[0:10]

        start = xpath.string('//Collected/Start_Date')
        end = xpath.string('//Collected/End_Date')
        if start is not None and end is not None:
            dataciteDates['collected'] = start + ' / ' + end

        self.metadata['dataciteDates'] = dataciteDates

        # Year of publication
        self.metadata['publicationYear'] = xpath.string('//Publication_Date')[0:4]

        # Rights
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
        westBoundLongitudes = xpath.strings('//geoLocation/westBoundLongitude')
        eastBoundLongitudes = xpath.strings('//geoLocation/eastBoundLongitude')
        southBoundLatitudes = xpath.strings('//geoLocation/southBoundLatitude')
        northBoundLatitudes = xpath.strings('//geoLocation/northBoundLatitude')

        # Bounding box: left,bottom,right,top
        boxes = []
        for west, south, east, north in zip(westBoundLongitudes, southBoundLatitudes, eastBoundLongitudes, northBoundLatitudes):
            box = ",".join([west, south, east, north])
            boxes.append(box)

        perioddates = [xpath.string('//Covered_Period/Start_Date'), xpath.string('//Covered_Period/End_Date')]
        period = "/".join([d for d in perioddates if d])

        if period and geoLocation:
            coverage = locations + [period] + boxes
        elif geoLocation:
            coverage = locations + boxes
        elif period:
            coverage = locations + [period]
        else:
            coverage = locations
        if coverage:
            self.metadata['coverage'] = coverage



