from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

class DataCite(object):
     """The standard Datacite.

     It is registered under the name 'datacite'
     """

     def __init__(self, prefix, config, db):
         self.prefix = prefix
         self.config = config
         self.db = db

         self.ns = {'datacite': 'http://datacite.org/schema/kernel-4'}
         self.schemas = {'datacite': 'http://schema.datacite.org/meta/kernel-4/metadata.xsd'}

     def get_namespace(self):
         return self.ns[self.prefix]

     def get_schema_location(self):
         return self.schemas[self.prefix]

     def __call__(self, element, metadata):
         data = metadata.record

         # TODO: is deze nog nodig?
         DATACITE =  ElementMaker(namespace=self.ns['datacite'],
                                nsmap =self.ns)
         NONE = ElementMaker('')

         datacite = NONE.resource()
         datacite.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
             self.ns['datacite'],
             self.schemas['datacite'])

         datacite.attrib['xmlns'] = self.ns['datacite']
         datacite.attrib['xmlnsxsi'] = XSI_NS

         language = data['metadata']['language'][0]

         # Identifier DOI
         try:
             identifier = NONE.identifier(data['metadata']['identifier'][0])
             identifier.attrib['identifyerType'] = "DOI" # TODO: Hardcoding allowed here?

             datacite.append(identifier)
         except KeyError:
             pass

         # Creators
         try:
             creators = NONE.creators()
             for dccreator in data['metadata']['dataciteCreators']:
                 creator = NONE.creator()
                 creator.append(NONE.creatorName(dccreator['name']))
                 #creator.append(NONE.givenName('Given'))
                 #creator.append(NONE.familyName('Family'))

                 nameIdentifier = NONE.nameIdentifier(dccreator['name_identifier'])
                 # nameIdentifier.attrib['schemeURI'] = 'http://orcid.org' ?????
                 nameIdentifier.attrib['nameIdentifierScheme'] = dccreator['name_identifier_scheme']
                 creator.append(nameIdentifier)

                 creator.append(NONE.affiliation(dccreator['affiliation']))

                 creators.append(creator)
             datacite.append(creators)
         except KeyError:
             pass

         # Title
         try:
             titles = NONE.titles()
             title = NONE.title(data['metadata']['title'][0])
             title.attrib['lang'] = language # 2do accepteert 'xml:lang' niet...moet anders opgevoerd
             titles.append(title)

             # TODO: Hier nog description toevoegen!
             datacite.append(titles)
         except KeyError:
             pass

         # Publisher
         try:
             datacite.append(NONE.publisher(data['metadata']['publisher']))
         except KeyError:
             pass

         # Publication year
         try:
             datacite.append(NONE.publicationYear(data['metadata']['publicationYear']))
         except KeyError:
             pass

         # Subjects
         try:
             subjects = NONE.subjects()
             for subject in  data['metadata']['subject']:
                 subjectNode = NONE.subject(subject)

                 subjectNode.attrib['lang'] = language # TODO: accepteert 'xml:lang' niet
                 subjectNode.attrib['schemeURI'] = 'http://orcid.org' #????
                 subjectNode.attrib['subjectScheme'] = 'dewey' #????

                 subjects.append(subjectNode)

             datacite.append(subjects)
         except KeyError:
             pass

         # Contributors
         try:
             contributors = NONE.contributors()
             for dccontributor in data['metadata']['dataciteContributors']:
                 contributor = NONE.contributor()
                 contributor.attrib['contributorType'] = dccontributor['type']
                 contributor.append(NONE.contributorName(dccontributor['name']))


                 nameIdentifier = NONE.nameIdentifier(dccontributor['name_identifier'])
                 # nameIdentifier.attrib['schemeURI'] = 'http://orcid.org' ?????
                 nameIdentifier.attrib['nameIdentifierScheme'] = dccontributor['name_identifier_scheme']
                 contributor.append(nameIdentifier)

                 # contributor.append(NONE.affiliation('Affiliation'))
                 contributors.append(contributor)
             datacite.append(contributors)
         except KeyError:
             pass

         # Date handling
         try:
             dataciteDates = NONE.dates()
             dateCollection = data['metadata']['dataciteDates']
             for dateType in dateCollection:
                 dataciteDate = NONE.date(dateCollection[dateType])
                 dataciteDate.attrib['dateType'] = dateType
                 dataciteDates.append(dataciteDate)
             datacite.append(dataciteDates)
         except KeyError:
             pass

         # Language
         try:
             datacite.append(NONE.language(language))
         except KeyError:
             pass

         # resourceType - hardcoded
         datacite.append(NONE.resourceType('Dataset'))

         # Related identifiers
         try:
             relatedIdentifiers = NONE.relatedIdentifiers()
             for identifier in data['metadata']['relatedIdentifiers']:
                 relatedIdentifier = NONE.relatedIdentifier(identifier['title'])
                 relatedIdentifier.attrib('relatedIdentifierType',identifier['relatedIdentifierType'])
                 relatedIdentifier.attrib('relationType',identifier['relatedType'])
                 relatedIdentifier.attrib('relation',identifier['relatedType'])


                 # relationType
                 # relatedIdentifier
                 # relatedIdentifierScheme

                 relatedIdentifiers.append(relatedIdentifier)

             datacite.append(relatedIdentifier)
         except KeyError:
             pass

         # Version
         try:
             datacite.append(NONE.version(data['metadata']['version']))
         except KeyError:
             pass

         # Rights
         try:
             rightsList = NONE.rightsList()
             rights = NONE.rightsList(data['metadata']['rights'][0])
             rights.attrib['rightsURI'] = 'http://creativecommons.org/publicdomain/zero/1.0/'
             rightsList.append(rights)
             datacite.append(rightsList)
         except KeyError:
             pass

         # Descriptions
         try:
             descriptions = NONE.descriptions()
             for description in data['metadata']['description']:
                 descriptionNode = NONE.description(description)

                 descriptionNode.attrib['lang'] = language # accepteert xml:lang niet
                 descriptionNode.attrib['descriptionType'] = 'Abstract'
                 descriptions.append(descriptionNode)

             datacite.append(descriptions)
         except KeyError:
             pass

         # Geolocations
         try:
             index = 2 # provision is set up this way - index=2 contains first geobox data
             geoLocations = NONE.geoLocations()

             while index<100:
                 if data['metadata']['coverage'][index]:
                     coverage = data['metadata']['coverage'][index].split(',')
                     geoLocation = NONE.geoLocation()
                     geoLocationBox = NONE.geoLocationBox()
                     geoLocationBox.append(NONE.westBoundLongitude(coverage[1]))
                     geoLocationBox.append(NONE.eastBoundLongitude(coverage[3]))
                     geoLocationBox.append(NONE.southBoundLatitude(coverage[2]))
                     geoLocationBox.append(NONE.northBoundLatitude(coverage[0]))

                     geoLocation.append(geoLocationBox)
                     geoLocations.append(geoLocation)

                     index += 1
         except IndexError:
             pass

         if index !=2:
             datacite.append(geoLocations)

         # Funding references
         try:
             fundingReferences = NONE.fundingReferences()
             for reference in data['metadata']['fundingReferences']:
                 fundingRef = NONE.fundingReference()
                 fundingRef.append(NONE.funderName(reference['name']))
                 fundingRef.append(NONE.Award_Number(reference['awardNumber']))

                 fundingReferences.append(fundingRef)

             datacite.append(fundingReferences)
         except KeyError:
             pass

         # Add entire structure
         element.append(datacite)
