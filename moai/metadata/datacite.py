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
             for creatorName in  data['metadata']['creator']:
                 creator = NONE.creator()
                 creator.append(NONE.creatorName(creatorName))
                 creator.append(NONE.givenName('Given'))
                 creator.append(NONE.familyName('Family'))

                 nameIdentifier = NONE.nameIdentifier('NameIdentifier')
                 nameIdentifier.attrib['schemeURI'] = 'http://orcid.org'
                 nameIdentifier.attrib['nameIdentifierScheme'] = 'ORCID'
                 creator.append(nameIdentifier)

                 creator.append(NONE.affiliation('Affiliation'))
                 creators.append(creator)

             datacite.append(creators)
         except KeyError:
             pass

         # Title
         try:
             titles = NONE.titles()
             title = NONE.title(data['metadata']['title'][0])
             title.attrib['lang'] = data['metadata']['language'][0] # accepteert xml:lang niet...moet anders opgevoerd
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

         #<publicationYear>2014</publicationYear>
         try:
             # TODO: fix bad argument type
             #datacite.append(NONE.publicationYear(data['metadata']['date']))
             pass
         except KeyError:
             pass

         # Subjects
         try:
             subjects = NONE.subjects()
             for subject in  data['metadata']['subject']:
                 subjectNode = NONE.subject(subject)

                 subjectNode.attrib['lang'] = data['metadata']['language'][0] # accepteert xml:lang niet
                 subjectNode.attrib['schemeURI'] = 'http://orcid.org' #????
                 subjectNode.attrib['subjectScheme'] = 'dewey' #????

                 subjects.append(subjectNode)

             datacite.append(subjects)
         except KeyError:
             pass

         # Contributors
         try:
             contributors = NONE.contributor()
             for contributorName in  data['metadata']['contributor']:
                 contributor = NONE.contributor()
                 contributor.attrib['contributorType'] = 'ProjectLeader'
                 contributor.append(NONE.contributorName(contributorName))

                 nameIdentifier = NONE.nameIdentifier('NameIdentifier')
                 nameIdentifier.attrib['schemeURI'] = 'http://orcid.org'
                 nameIdentifier.attrib['nameIdentifierScheme'] = 'ORCID'
                 contributor.append(nameIdentifier)

                 contributor.append(NONE.affiliation('Affiliation'))
                 contributors.append(contributor)
             datacite.append(contributors)
         except KeyError:
             pass

         # Dates
         try:
             dates = NONE.dates()
             for date in  data['metadata']['date']:
                 dateNode = NONE.date(date)
                 dateNode.attrib['dateType'] = '??'

                 dates.append(dateNode)
             datacite.append(dates)
         except KeyError:
             pass

         # Language
         try:
             datacite.append(NONE.language(data['metadata']['language'][0]))
         except KeyError:
             pass

         # Version
         try:
             datacite.append(NONE.version('VERSION??'))
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

                 descriptionNode.attrib['lang'] = data['metadata']['language'][0] # accepteert xml:lang niet
                 descriptionNode.attrib['descriptionType'] = 'Abstract'
                 descriptions.append(descriptionNode)

             datacite.append(descriptions)
         except KeyError:
             pass

         # Geolocations
         try:
             geoLocations = NONE.geoLocations()

             # TODO: Loop, can be multiple????
             coverage = data['metadata']['coverage'][2].split(',')
             geoLocation = NONE.geoLocation()
             geoLocationBox = NONE.geoLocationBox()
             geoLocationBox.append(NONE.westBoundLongitude(coverage[1]))
             geoLocationBox.append(NONE.eastBoundLongitude(coverage[3]))
             geoLocationBox.append(NONE.southBoundLatitude(coverage[2]))
             geoLocationBox.append(NONE.northBoundLatitude(coverage[0]))

             geoLocation.append(geoLocationBox)
             geoLocations.append(geoLocation)

             datacite.append(geoLocations)
         except KeyError:
             pass

         # Add entire structure
         element.append(datacite)
