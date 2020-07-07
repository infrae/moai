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
                    'oai_datacite': 'http://datacite.org/schema/kernel-4'}
         self.schemas = {'datacite': 'http://schema.datacite.org/meta/kernel-4/metadata.xsd',
                         'oai_datacite': 'http://schema.datacite.org/meta/kernel-4/metadata.xsd'}

     def get_namespace(self):
         return self.ns[self.prefix]

     def get_schema_location(self):
         return self.schemas[self.prefix]

     def __call__(self, element, metadata):
         try:
             data = metadata.record['metadata']['metadata']
         except:
             pass

         # TODO: is deze nog nodig?
         DATACITE =  ElementMaker(namespace=self.ns['datacite'],
                                nsmap =self.ns)
         NONE = DATACITE #ElementMaker('', nsmap = self.ns)

         datacite = NONE.resource()
         datacite.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
             self.ns['datacite'],
             self.schemas['datacite'])

         # Language
         try:
            language = data['Language'][0:2]
         except (IndexError, KeyError) as e:
            language = 'en'  # Default language hardcoded for now
            pass


         # Identifier DOI
         try:
             identifier = NONE.identifier(data['System']['Persistent_Identifier_Datapackage']['Identifier'])
             identifier.attrib['identifierType'] = "DOI"
             datacite.append(identifier)
         except (IndexError, KeyError) as e:
             pass

         # Creators
         try:
             creators = NONE.creators()

             creator_list = data['Creator']
             if isinstance(creator_list, list)==False:
                 creator_list = [creator_list]

             for dccreator in creator_list:
                 creator = NONE.creator()

                 name = dccreator['Name']['First_Name'] + ' ' +  dccreator['Name']['Last_Name']
                 creator.append(NONE.creatorName(name))

                 affiliation_list = dccreator['Affiliation']
                 if isinstance(affiliation_list, list)==False:
                     affiliation_list = [affiliation_list]

                 for affiliation in affiliation_list:
                     creator.append(NONE.affiliation(affiliation))

                 idf_list =  dccreator['Person_Identifier']
                 if isinstance(idf_list, list)==False:
		     idf_list = [idf_list]
                 for identifier in idf_list:
                     nameIdf = NONE.nameIdentifier(identifier['Name_Identifier'])
                     nameIdf.attrib['nameIdentifierScheme'] = identifier['Name_Identifier_Scheme']
                     creator.append(nameIdf)

                 creators.append(creator)
             datacite.append(creators)
         except KeyError:
             pass

         # Title
         try:
             titles = NONE.titles()
             title = NONE.title(data['Title'])
             title.attrib['{%s}lang' % XML_NS] = language
             titles.append(title)
             datacite.append(titles)
         except (IndexError,KeyError) as e:
             pass

         # Publisher - hardcoded
         try:
             if data['Title']:
                 datacite.append(NONE.publisher('Utrecht University'))
         except KeyError:
             pass

         # Publication year
         try:
             datacite.append(NONE.publicationYear(data['System']['Publication_Date'][0:4]))
         except KeyError:
             pass

         # Subjects divided in three steps: disciplines, tags and collection name!
         try:
             subjects = NONE.subjects()

             # Subjects - Disciplines
             list_subjects = data['Discipline']
             if isinstance(list_subjects, list)==False:
                 list_subjects = [list_subjects]
             for subject in list_subjects:
                 subjectNode = NONE.subject(subject)
                 subjectNode.attrib['subjectScheme'] = 'OECD FOS 2007'
                 subjects.append(subjectNode)

             datacite.append(subjects)


             # Subjects - Tags
             list_subjects = data['Tag']
             if isinstance(list_subjects, list)==False:
                 list_subjects = [list_subjects]
             for subject in list_subjects:
                 subjectNode = NONE.subject(subject)
                 subjectNode.attrib['subjectScheme'] = 'Keyword'
                 subjects.append(subjectNode)


             # Subjects - Collection name
             subjectNode = NONE.subject( data['Collection_Name'])
             subjectNode.attrib['subjectScheme'] = 'collection'
             subjects.append(subjectNode)

             datacite.append(subjects)
         except KeyError:
             pass

         # Subject - special fields geo schemas
         # To BE DONE
         subject_fields = ["Main_Setting",
            "Process_Hazard",
            "Geological_Structure",
            "Geomorphical_Feature",
            "Material",
            "Apparatus",
            "Monitoring",
            "Software",
            "Measured_Property"]

	 for subject_field in subject_fields:
             try:
                 list_subjects = data[subject_field]
                 if isinstance(list_subjects, list)==False:
                     list_subjects = [list_subjects]
                 for subject in list_subjects:
                     if isinstance(subject, basestring) and len(subject):
		         subjectNode = NONE.subject(subject)
                         subjectNode.attrib['subjectScheme'] = subject_field
                         subjects.append(subjectNode)

             except KeyError:
                 continue

         # Contributors
         try:
             contributors = NONE.contributors()

             contributor_list = data['Contributor']
             if isinstance(contributor_list, list)==False:
                 contributor_list = [contributor_list]

             for dccontributor in contributor_list:
                 contributor = NONE.contributor()
                 try: # not present in GEO schemas
                     contributor.attrib['contributorType'] = dccontributor['Contributor_Type']
		 except KeyError:
                     pass

                 name = dccontributor['Name']['First_Name'] + ' ' + dccontributor['Name']['Last_Name']
                 contributor.append(NONE.contributorName(name))

                 affiliation_list = dccontributor['Affiliation']
                 if isinstance(affiliation_list, list)==False:
                     affiliation_list = [affiliation_list]

                 for affiliation in affiliation_list:
                     contributor.append(NONE.affiliation(affiliation))

                 idf_list =  dccontributor['Person_Identifier']
                 if isinstance(idf_list, list)==False:
                     idf_list = [idf_list]
                 for identifier in idf_list:
                     nameIdf = NONE.nameIdentifier(identifier['Name_Identifier'])
                     nameIdf.attrib['nameIdentifierScheme'] = identifier['Name_Identifier_Scheme']
                     contributor.append(nameIdf)

                 contributors.append(contributor)

	     # GEO 'Contact person' is a special case of contributerType: contactPerson
             try:
                 contributor_list = data['Contact']
                 if isinstance(contributor_list, list)==False:
                     contributor_list = [contributor_list]
                 for dccontributor in contributor_list:
                     contributor = NONE.contributor()
                     contributor.attrib['contributorType'] = 'ContactPerson'
                     name = dccontributor['Name']['First_Name'] + ' ' + dccontributor['Name']['Last_Name']
                     contributor.append(NONE.contributorName(name))

                     affiliation_list = dccontributor['Affiliation']
                     if isinstance(affiliation_list, list)==False:
                         affiliation_list = [affiliation_list]

                     for affiliation in affiliation_list:
                         contributor.append(NONE.affiliation(affiliation))

                     idf_list =  dccontributor['Person_Identifier']
                     if isinstance(idf_list, list)==False:
                         idf_list = [idf_list]
                     for identifier in idf_list:
                         nameIdf = NONE.nameIdentifier(identifier['Name_Identifier'])
                         nameIdf.attrib['nameIdentifierScheme'] = identifier['Name_Identifier_Scheme']
                         contributor.append(nameIdf)

                     contributors.append(contributor)
             except KeyError:
                 pass


             datacite.append(contributors)
         except KeyError:
             pass

         # Date handling
         # -Updated
         dataciteDates = NONE.dates()
         try:
             date = data['System']['Last_Modified_Date']
             dataciteDate = NONE.date(date)
             dataciteDate.attrib['dateType'] = 'Updated'
             dataciteDates.append(dataciteDate)
             datacite.append(dataciteDates)
         except KeyError:
             pass

         # -Available
         try:
             date = data['Embargo_End_Date']
             dataciteDate = NONE.date(date)
             dataciteDate.attrib['dateType'] = 'Available'
             dataciteDates.append(dataciteDate)
             datacite.append(dataciteDates)
         except KeyError:
             pass

         # -Start / end collected
         try:
             date_start = data['Collected']['Start_Date']
             date_end   = data['Collected']['End_Date']
             dataciteDate = NONE.date(date_start + '/' + date_end)
             dataciteDate.attrib['dateType'] = 'Collection'
             dataciteDates.append(dataciteDate)
             datacite.append(dataciteDates)
         except KeyError:
             pass

         datacite.append(dataciteDates)

         # Language
         try:
             datacite.append(NONE.language(language))
         except KeyError:
             pass

         # ResourceType

         # List as defined by Ton/Maarten/Frans 20190603
         dictResourceTypes = {'Dataset'  : 'Research Data',
                              'DataPaper': 'Method Description',
                              'Software' : 'Computer Code',
                              'Text'     : 'Other Document'}

         try:
             resourceTypeGeneral = data['Data_Type']
             resourceTypeLabel = dictResourceTypes[resourceTypeGeneral]
             resourceType = NONE.resourceType(resourceTypeLabel)
             resourceType.attrib['resourceTypeGeneral'] = resourceTypeGeneral
             datacite.append(resourceType)
         except KeyError:
	     resourceType = NONE.resourceType('Other Document')
             resourceType.attrib['resourceTypeGeneral'] = 'Text'
             datacite.append(resourceType)
             pass

         # Related identifiers
         try:
             relatedIdentifiers = NONE.relatedIdentifiers()
             for identifier in data['Related_Datapackage']:
                 relatedIdentifier = NONE.relatedIdentifier(identifier['Persistent_Identifier']['Identifier'])
                 relatedIdentifier.attrib['relatedIdentifierType'] = identifier['Persistent_Identifier']['Identifier_Scheme']
                 relatedIdentifier.attrib['relationType'] = identifier['Relation_Type'].split(':')[0]
                 relatedIdentifiers.append(relatedIdentifier)

             datacite.append(relatedIdentifiers)
         except KeyError:
             pass

         # Version
         try:
             datacite.append(NONE.version(data['Version']))
         except KeyError:
             pass

         # Rights
         try:
             license = data['License']
             license_uri = data['System']['License_URI']

             access_restriction = data['Data_Access_Restriction']
             access_rights = ''
	     access_rightsURI = ''
	     if access_restriction:
                 if access_restriction.startswith('Open'):
                     access_rights = 'Open Access'
                     access_rightsURI = 'info:eu-repo/semantics/openAccess'
                 elif access_restriction.startswith('Restricted'):
                     access_rights = 'Restricted Access'
                     access_rightsURI = 'info:eu-repo/semantics/restrictedAccess'
                 elif access_restriction.startswith('Closed'):
                     access_rights = 'Closed Access'
                     access_rightsURI = 'info:eu-repo/semantics/closedAccess'

             rightsList = NONE.rightsList()
             rights = NONE.rights(license)
             rights.attrib['rightsURI'] = license_uri
             rightsList.append(rights)
             rights = NONE.rights(access_rights)
             rights.attrib['rightsURI'] = access_rightsURI
             rightsList.append(rights)
             datacite.append(rightsList)
         except (IndexError, KeyError) as e:
             pass

         # Descriptions
         try:
             descriptions = NONE.descriptions()
             descriptionNode = NONE.description(data['Description'])
             descriptionNode.attrib['descriptionType'] = 'Abstract'
             descriptions.append(descriptionNode)

             datacite.append(descriptions)
         except KeyError:
             pass


	 # GeoLocation
         try:
             geoLocations = NONE.geoLocations()
             location_present = False
             for geoloc in data['GeoLocation']:
                 location_present = True
                 temp_description_start = geoloc['Description_Temporal']['Start_Date']
                 temp_description_end = geoloc['Description_Temporal']['End_Date']
                 spatial_description = geoloc['Description_Spatial']

                 lon0 = str(geoloc['geoLocationBox']['westBoundLongitude'])
                 lat0 = str(geoloc['geoLocationBox']['northBoundLatitude'])
                 lon1 = str(geoloc['geoLocationBox']['eastBoundLongitude'])
                 lat1 = str(geoloc['geoLocationBox']['southBoundLatitude'])

                 geoLocation = NONE.geoLocation()

                 if spatial_description:
                     geoLocationPlace = NONE.geoLocationPlace(spatial_description)
                     geoLocation.append(geoLocationPlace)

                 if lon0==lon1 and lat0==lat1: # dealing with a point
                     geoLocationPoint = NONE.geoLocationPoint()
                     geoLocationPoint.append(NONE.pointLongitude(lon0))
                     geoLocationPoint.append(NONE.pointLatitude(lat0))
                     geoLocation.append(geoLocationPoint)
                 else:
                     geoLocationBox = NONE.geoLocationBox()
                     geoLocationBox.append(NONE.westBoundLongitude(lon0))
                     geoLocationBox.append(NONE.eastBoundLongitude(lon1))
                     geoLocationBox.append(NONE.southBoundLatitude(lat0))
                     geoLocationBox.append(NONE.northBoundLatitude(lat1))
                     geoLocation.append(geoLocationBox)

                 geoLocations.append(geoLocation)

             # alleen toevoegen als er werkelijk locaties zijn
             if location_present:
                 datacite.append(geoLocations)

         except (IndexError, KeyError) as e:
             pass

         # OK Funding references
         try:
             fundingReferences = NONE.fundingReferences()
             for reference in data['Funding_Reference']:
                 fundingRef = NONE.fundingReference()
                 fundingRef.append(NONE.funderName(reference['Funder_Name']))
                 try:
                     fundingRef.append(NONE.awardNumber(reference['Award_Number']))
                 except KeyError:
                     pass
                 fundingReferences.append(fundingRef)

             datacite.append(fundingReferences)
         except KeyError:
             pass

         # Add entire structure
         element.append(datacite)
