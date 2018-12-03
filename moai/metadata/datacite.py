from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
XML_NS = 'https://www.w3.org/TR/xml-names/'

class DataCite(object):
     """The standard Datacite.

     It is registered under the name 'datacite'
     """

     def __init__(self, prefix, config, db):
         self.prefix = prefix
         self.config = config
         self.db = db

         self.ns = {'datacite': 'http://datacite.org/schema/kernel-4',
                    'xml': XML_NS
         }
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
         NONE = DATACITE #ElementMaker('', nsmap = self.ns)

         datacite = NONE.resource()
         datacite.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
             self.ns['datacite'],
             self.schemas['datacite'])

         try:
            language = data['metadata']['language'][0]
         except (IndexError, KeyError) as e:
            language = 'en'  # Default language hardcoded for now
            pass

         # Identifier DOI
         try:
             identifier = NONE.identifier(data['metadata']['identifier'][0])
             identifier.attrib['identifierType'] = "DOI"
             datacite.append(identifier)
         except (IndexError, KeyError) as e:
             pass

         # Creators
         try:
             creators = NONE.creators()
             for dccreator in data['metadata']['dataciteCreators']:
                 creator = NONE.creator()
                 creator.append(NONE.creatorName(dccreator['name']))
                 #creator.append(NONE.givenName('Given'))
                 #creator.append(NONE.familyName('Family'))

                 if 'affiliation' in dccreator:
                     for creatorAffiliation in dccreator['affiliation']:
                         creator.append(NONE.affiliation(creatorAffiliation))

                 for nameIdentifier in dccreator['name_identifiers']:
                     for key in nameIdentifier:
                        nameIdf = NONE.nameIdentifier(nameIdentifier[key])
                        nameIdf.attrib['nameIdentifierScheme'] = key
                        creator.append(nameIdf)

                 creators.append(creator)
             datacite.append(creators)
         except KeyError:
             pass

         # Title
         try:
             titles = NONE.titles()
             title = NONE.title(data['metadata']['title'][0])
             title.attrib['{%s}lang' % XML_NS] = language
             titles.append(title)
             datacite.append(titles)
         except (IndexError,KeyError) as e:
             pass

         # Publisher - hardcoded
         try:
             datacite.append(NONE.publisher('Utrecht University'))
         except KeyError:
             pass

         # Publication year
         try:
             datacite.append(NONE.publicationYear(data['metadata']['publicationYear']))
         except KeyError:
             pass

         # Subjects divided in three steps: disciplines, tags and collection name!
         try:
             subjects = NONE.subjects()
             # Subjects - Disciplines
             for subject in  data['metadata']['dataciteDisciplines']:
                 subjectNode = NONE.subject(subject)
                 subjectNode.attrib['subjectScheme'] = 'OECD FOS 2007'
                 subjects.append(subjectNode)

             # Subjects - Tags
             for subject in  data['metadata']['dataciteTags']:
                 subjectNode = NONE.subject(subject)
                 subjectNode.attrib['subjectScheme'] = 'Keyword'
                 subjects.append(subjectNode)

             # Subjects - Collection name 
             for subject in  data['metadata']['collectionName']:
                 subjectNode = NONE.subject(subject)
                 subjectNode.attrib['subjectScheme'] = 'collection'
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

                 # contributor.append(NONE.affiliation('Affiliation'))
                 if 'affiliation' in dccontributor:
                     # contributor.append(NONE.affiliation(dccontributor['affiliation']))
                     for contribAffiliation in dccontributor['affiliation']:
                         contributor.append(NONE.affiliation(contribAffiliation))


                 for nameIdentifier in dccontributor['name_identifiers']:
                     for key in nameIdentifier:
                        # contributor.append(NONE.idftest(key))
                        nameIdf = NONE.nameIdentifier(nameIdentifier[key])
                        nameIdf.attrib['nameIdentifierScheme'] = key
                        contributor.append(nameIdf)

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
         resourceType = NONE.resourceType('Dataset')
         resourceType.attrib['resourceTypeGeneral'] = 'Dataset'
         datacite.append(resourceType)

         # Related identifiers
         try:
             relatedIdentifiers = NONE.relatedIdentifiers()
             for identifier in data['metadata']['relatedIdentifiers']:
                 relatedIdentifier = NONE.relatedIdentifier(identifier['title'])
                 relatedIdentifier.attrib['relatedIdentifierType'] = identifier['relatedIdentifierScheme']
                 relatedIdentifier.attrib['relationType'] = identifier['relationType'].split(':')[0]
                 relatedIdentifier.attrib['relatedIdentifier'] = identifier['relatedIdentifier']

                 # relationType
                 # relatedIdentifier
                 # relatedIdentifierScheme

                 relatedIdentifiers.append(relatedIdentifier)

             datacite.append(relatedIdentifiers)
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
             rights = NONE.rights(data['metadata']['rights'][0])
             rights.attrib['rightsURI'] = data['metadata']['rightsLicenseURL']
             rightsList.append(rights)
             rights = NONE.rights(data['metadata']['accessRights'])
             rights.attrib['rightsURI'] = data['metadata']['accessRightsURI']
             rightsList.append(rights)
             datacite.append(rightsList)
         except (IndexError, KeyError) as e:
             pass
			 
         # Descriptions
         try:
             descriptions = NONE.descriptions()
             for description in data['metadata']['description']:
                 descriptionNode = NONE.description(description)
                 descriptionNode.attrib['descriptionType'] = 'Abstract'
                 descriptions.append(descriptionNode)

             datacite.append(descriptions)
         except KeyError:
             pass

         # Geolocations
         try:
             geoLocations = NONE.geoLocations()

             # "dataciteLocations"

             addGeoLocations = False
             # Look at location names contained in one string
             locations =  data['metadata']['dataciteLocations']
             locationCount = 0
             for location in locations:
                 geoLocation = NONE.geoLocation()
                 geoLocationPlace = NONE.geoLocationPlace(location)
                 geoLocation.append(geoLocationPlace)
                 geoLocations.append(geoLocation)
                 addGeoLocations = True
                 locationCount += 1

             # Look at geo boxes - At the moment this is NOT part of iLab.
             # Needs to be fixed for EPOS
#             index = 2 # provision is set up this way - index=2 contains first geobox data
             # Must be made flexible - possibly on the count of dataciteLocations
             # geoLocations = NONE.geoLocations()

#             while index<100:
#                 if data['metadata']['coverage'][index]:
#                     coverage = data['metadata']['coverage'][index].split(',')
#                     geoLocation = NONE.geoLocation()
#                     geoLocationBox = NONE.geoLocationBox()
#                     geoLocationBox.append(NONE.westBoundLongitude(coverage[0]))
#                     geoLocationBox.append(NONE.eastBoundLongitude(coverage[2]))
#                     geoLocationBox.append(NONE.southBoundLatitude(coverage[1]))
#                     geoLocationBox.append(NONE.northBoundLatitude(coverage[3]))

#                     geoLocation.append(geoLocationBox)
#                     geoLocations.append(geoLocation)

#                    addGeoLocations = True
#                     index += 1
         except (IndexError, KeyError) as e:
             pass

         if addGeoLocations:
             datacite.append(geoLocations)

         # Funding references
         try:
             fundingReferences = NONE.fundingReferences()
             for reference in data['metadata']['fundingReferences']:
                 fundingRef = NONE.fundingReference()
                 fundingRef.append(NONE.funderName(reference['name']))
                 fundingRef.append(NONE.awardNumber(reference['awardNumber']))
                 fundingReferences.append(fundingRef)

             datacite.append(fundingReferences)
         except KeyError:
             pass

         # Add entire structure
         element.append(datacite)
