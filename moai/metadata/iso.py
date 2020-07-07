from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

class Iso(object):
     """The standard ISO19139.

     It is registered under the name 'iso19139'
     """

     def __init__(self, prefix, config, db):
         self.prefix = prefix
         self.config = config
         self.db = db

         self.ns =   {'iso19139': 'http://www.isotc211.org/2005/gmd',
                      'gmd': 'http://www.isotc211.org/2005/gmd',
                      'gco': 'http://www.isotc211.org/2005/gco',
                      'gmx': 'http://www.isotc211.org/2005/gmx',
                      'gml': 'http://www.opengis.net/gml/3.2',
                      'xlink': 'http://www.w3.org/1999/xlink',
                      'xsi':  'http://www.w3.org/2001/XMLSchema-instance'
         }

         self.schemas = {'iso': 'http://www.isotc211.org/2005/gmd/gmd.xsd',
                         'iso19139': 'http://www.isotc211.org/2005/gmd/gmd.xsd'}

     def get_namespace(self):
         return self.ns[self.prefix]

     def get_schema_location(self):
         return self.schemas[self.prefix]

     def __call__(self, element, metadata):
         try:
             data = metadata.record['metadata']['metadata']
         except:
             pass

         # Is deze nog nodig?????
         # Basic - will this be used as all will be GMD
         #NONE =  ElementMaker(namespace=self.ns['gmd'],
         #                    nsmap =self.ns)

         # GMD based elements
         GMD = ElementMaker(namespace=self.ns['gmd'],
                             nsmap =self.ns)
         # GCO based elements
         GCO = ElementMaker(namespace=self.ns['gco'],
                             nsmap =self.ns)

         iso = GMD.MD_Metadata()
         iso.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
             self.ns['xsi'],
             self.schemas['iso'])


         # Language
         try:
             languageVal = data['Language'][0:3]
         except (IndexError, KeyError) as e:
             languageVal = 'eng'  # Default language hardcoded for now
             pass



# DOI
         fileIdentifier = GMD.fileIdentifier()
         fileIdentifier.append(GCO.CharacterString('doi:'+data['System']['Persistent_Identifier_Datapackage']['Identifier']))
         iso.append(fileIdentifier)

# Language
         language = GMD.language()
         LanguageCode = GMD.LanuageCode(languageVal)
         LanguageCode.attrib['codeList'] = 'http://www.loc.gov/standards/iso639-2/'
         LanguageCode.attrib['codeListValue'] = languageVal

         language.append(LanguageCode)
         iso.append(language)

# Publisher - Hardcoded
         contact = GMD.contact()

         CI_ResponsibleParty = GMD.CI_ResponsibleParty()
         contactInfo = GMD.contactInfo()
         CI_Contact = GMD.CI_Contact()
         onlineResource = GMD.onlineResource()
         CI_OnlineResource = GMD.CI_OnlineResource()
         linkage = GMD.linkage()
         URL = GMD.URL('Utrecht University')

         linkage.append(URL)
         CI_OnlineResource.append(linkage)
         onlineResource.append(CI_OnlineResource)
         CI_Contact.append(onlineResource)
         contactInfo.append(CI_Contact)
         CI_ResponsibleParty.append(contactInfo)

         # Add to main level - contact
         contact.append(CI_ResponsibleParty)

         iso.append(contact)


# Create base nodes
         identificationInfo = GMD.identificationInfo()

         MD_DataIdentification = GMD.MD_DataIdentification()


         citation = GMD.citation()


         CI_Citation = GMD.CI_Citation()


# TITLE
         title = GMD.title()

         try:
             CharacterString = GCO.CharacterString(data['Title'])
             title.append(CharacterString)

             CI_Citation.append(title)

         except (IndexError,KeyError) as e:
             pass


# DATE HANDLING
         try:
             # The dicts assume, for now, that only one date of each datetype will exist.
             dates = {'revision': data['System']['Last_Modified_Date'],
                      'creation': data['System']['Publication_Date'][0:4]}

             for dateTypeCode,thedate in dates.items():
                 datelevel1 = GMD.date()
                 CI_Date = GMD.CI_Date()
                 datelevel2 =  GMD.date()

                 # dateTypeCode = 'revision'
                 CI_DateTypeCode = GMD.CI_DateTypeCode(dateTypeCode)
                 CI_DateTypeCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_DateTypeCode'
                 CI_DateTypeCode.attrib['codeListValue'] = dateTypeCode

                 datelevel2.append(GCO.Date(thedate))
                 datelevel2.append(CI_DateTypeCode)

                 CI_Date.append(datelevel2)
                 datelevel1.append(CI_Date)
                 CI_Citation.append(CI_Date)

         except (IndexError,KeyError) as e:
             pass

# DOI
         try:
             identifier = GMD.identifier()
             MD_Identifier = GMD.MD_Identifier()
             code = GMD.code()
             CharacterString = GCO.CharacterString(data['System']['Persistent_Identifier_Datapackage']['Identifier'])
             code.append(CharacterString)
             MD_Identifier.append(code)
             identifier.append(MD_Identifier)

             CI_Citation.append(identifier)

         except (IndexError, KeyError) as e:
             pass


# Author / Creator
          # Role 'author' can be hardcoded. Will not change

         role = GMD.role()
         CI_RoleCode = GMD.CI_RoleCode('author') # Can be hardcoded
         CI_RoleCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
         CI_RoleCode.attrib['codeListValue'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode_author'
         role.append(CI_RoleCode)

         try:
             creator_list = data['Creator']
             if isinstance(creator_list, list)==False:
                 creator_list = [creator_list]

             for dccreator in creator_list:
                 citedResponsibleParty = GMD.citedResponsibleParty()
                 CI_ResponsibleParty = GMD.CI_ResponsibleParty()

                 individualName = dccreator['Name']['First_Name'] + ' ' +  dccreator['Name']['Last_Name']
                 CI_ResponsibleParty.append(GMD.individualName(GCO.CharacterString(individualName)))


                 affiliation_list = dccreator['Affiliation']
                 if isinstance(affiliation_list, list)==False:
                     affiliation_list = [affiliation_list]

                 for affiliation in affiliation_list:
                     CI_ResponsibleParty.append(GMD.organisationName(GCO.CharacterString(affiliation)))

                 CI_ResponsibleParty.append(role)

                 citedResponsibleParty.append(CI_ResponsibleParty)

                 CI_Citation.append(citedResponsibleParty)

         except KeyError:
             pass

# Funder
         role = GMD.role()
         CI_RoleCode = GMD.CI_RoleCode('funder') # Hardcoded
         CI_RoleCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
         CI_RoleCode.attrib['codeListValue'] = '"http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode_funder'
         role.append(CI_RoleCode)

         try:
             funder_list = data['Funding_Reference']
             if isinstance(funder_list, list)==False:
                 funder_list = [funder_list]

             for funder in funder_list:
                 citedResponsibleParty = GMD.citedResponsibleParty()
                 CI_ResponsibleParty = GMD.CI_ResponsibleParty()

                 organisationName = GMD.organisationName()
                 organisationName.append(GCO.CharacterString(funder['Funder_Name']))

                 CI_ResponsibleParty.append(organisationName)

                 CI_ResponsibleParty.append(role)

                 citedResponsibleParty.append(CI_ResponsibleParty)

                 CI_Citation.append(citedResponsibleParty)
         except KeyError:
             pass

# Contributors
         role = GMD.role()
         CI_RoleCode = GMD.CI_RoleCode('contributor') # Hardcoded for now
         CI_RoleCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
         CI_RoleCode.attrib['codeListValue'] = '"http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode_contributor'
         role.append(CI_RoleCode)

         try:
             contributor_list = data['Contributor']
             if isinstance(contributor_list, list)==False:
                 contributor_list = [contributor_list]

             for contrib in contributor_list:
                 citedResponsibleParty = GMD.citedResponsibleParty()
                 CI_ResponsibleParty = GMD.CI_ResponsibleParty()

                 individualName = contrib['Name']['First_Name'] + ' ' +  contrib['Name']['Last_Name']
                 CI_ResponsibleParty.append(GMD.individualName(GCO.CharacterString(individualName)))


                 affiliation_list = contrib['Affiliation']
                 if isinstance(affiliation_list, list)==False:
                     affiliation_list = [affiliation_list]

                 for affiliation in affiliation_list:
                     CI_ResponsibleParty.append(GMD.organisationName(GCO.CharacterString(affiliation)))

                 CI_ResponsibleParty.append(role)

                 citedResponsibleParty.append(CI_ResponsibleParty)

                 CI_Citation.append(citedResponsibleParty)
         except KeyError:
             pass

## citation level is complete - add all
         citation.append(CI_Citation)

         MD_DataIdentification.append(citation)

# description - onder MD_DataIdentification
         try:
             abstract = GMD.abstract()
             CharacterString = GCO.CharacterString(data['Description'])
             abstract.append(CharacterString)

             MD_DataIdentification.append(abstract)
         except (IndexError,KeyError) as e:
             pass

# pointOfContact
# CONTACT PERSONS   ONDER MD_DataIdentification
         pointOfContact = GMD.pointOfContact()

         role = GMD.role()
         CI_RoleCode = GMD.CI_RoleCode('pointOfContact')
         CI_RoleCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode'
         CI_RoleCode.attrib['codeListValue'] = '"http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode_pointOfContact'
         role.append(CI_RoleCode)

         try:
             # GEO 'Contact person' is a special case of contributerType: contactPerson

             contributor_list = data['Contact']
             if isinstance(contributor_list, list)==False:
                 contributor_list = [contributor_list]

             for dccontributor in contributor_list:
                 CI_ResponsibleParty = GMD.CI_ResponsibleParty()

                 individualName = dccreator['Name']['First_Name'] + ' ' +  dccreator['Name']['Last_Name']
                 CI_ResponsibleParty.append(GMD.individualName(GCO.CharacterString(individualName)))

                 affiliation_list = dccontributor['Affiliation']
                 if isinstance(affiliation_list, list)==False:
                     affiliation_list = [affiliation_list]

                 for affiliation in affiliation_list:
                     CI_ResponsibleParty.append(GMD.organisationName(GCO.CharacterString(affiliation)))

                 CI_ResponsibleParty.append(role)
                 pointOfContact.append(CI_ResponsibleParty)

                 MD_DataIdentification.append(pointOfContact)

         except (IndexError,KeyError) as e:
             pass


# Keywords
# Tags and disciplines - sluit aan op level MD_DataIdentification

         # DISCIPLINES - all in 1 set
         try:
             descriptiveKeywords = GMD.descriptiveKeywords() # Base of each keyword alike type
             MD_Keywords = GMD.MD_Keywords()

             # Keep the listed values as one set of decriptiveKeywords

             # Subjects - Disciplines
             list_subjects = data['Discipline']
             if isinstance(list_subjects, list)==False:
                 list_subjects = [list_subjects]
             for subject in list_subjects:
                 keyword = GMD.keyword()
                 CharacterString = GCO.CharacterString(subject)
                 keyword.append(CharacterString)
                 MD_Keywords.append(keyword)

             # Add Discipline as keywords
             descriptiveKeywords.append(MD_Keywords)
             MD_DataIdentification.append(descriptiveKeywords)

         except (IndexError,KeyError) as e:
             pass


         # Add Discipline as keywords
         MD_DataIdentification.append(MD_Keywords)

         # TAGS - all in 1 set
         try:
             descriptiveKeywords = GMD.descriptiveKeywords() # Base of each keyword alike type
             MD_Keywords = GMD.MD_Keywords()

             # Subjects - Tags
             list_subjects = data['Tag']
             if isinstance(list_subjects, list)==False:
                 list_subjects = [list_subjects]
             for subject in list_subjects:
                 keyword = GMD.keyword()
                 CharacterString = GCO.CharacterString(subject)
                 keyword.append(CharacterString)
                 MD_Keywords.append(keyword)

             # Add Tags as keywords
             descriptiveKeywords.append(MD_Keywords)
             MD_DataIdentification.append(descriptiveKeywords)

         except (IndexError,KeyError) as e:
             pass


         # Next descriptipe Keyword set  COLLECTION NAME (=ILAB)
         try:
             descriptiveKeywords = GMD.descriptiveKeywords() # Base of the keywords loop.
             MD_Keywords = GMD.MD_Keywords()

             # Subjects - Collection name
             keyword = GMD.keyword()
             CharacterString = GCO.CharacterString(data['Collection_Name'])
             keyword.append(CharacterString)
             MD_Keywords.append(keyword)

             descriptiveKeywords.append(MD_Keywords)
             MD_DataIdentification.append(descriptiveKeywords)

         except (IndexError,KeyError) as e:
             pass

         # Next descriptipe Keyword set  GEO SPECIFIC
         descriptiveKeywords = GMD.descriptiveKeywords() # Base of the keywords loop.
         MD_Keywords = GMD.MD_Keywords()

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
                 subject_counter = 0
                 for subject in list_subjects:
                     if isinstance(subject, basestring) and len(subject):
                         subject_counter += 1
                         keyword = GMD.keyword()
                         CharacterString = GCO.CharacterString(subject)
                         keyword.append(CharacterString)
                         MD_Keywords.append(keyword)

                 # Add Tags as keywords
                 if subject_counter:
                     descriptiveKeywords.append(MD_Keywords)
                     MD_DataIdentification.append(descriptiveKeywords)

             except KeyError:
                 continue

## RIGHTS
         # Transform Yoda to ISO classification codes
         classCode = {'Public':'unclassified',
                'Basic':'restricted',
                'Sensitive':'confidential',
                'Critical':'topSecret'
         }

         try:
             securityClassCode = classCode[data['Data_Classification']]

             MD_ClassificationCode = GMD.MD_ClassificationCode()
             MD_ClassificationCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/codeList.xml#MD_ClassificationCode'
             MD_ClassificationCode.attrib['codeListValue'] = securityClassCode

         except (IndexError, KeyError) as e:
             pass

         # Resource contstraints
         try:
             license = data['License']
             license_uri = data['System']['License_URI']

             resourceConstraints = GMD.resourceConstraints()
             resourceConstraints.attrib['xlink']=license_uri
             MD_Constraints = GMD.MD_Constraints()
             useLimitation = GMD.useLimitation()
             useLimitation.append(GCO.CharacterString(license))
             MD_Constraints.append(useLimitation)
             resourceConstraints.append(MD_Constraints)

             MD_DataIdentification.append(resourceConstraints)

         except (IndexError, KeyError) as e:
             pass


         # Legal constraints
         try:
             access_restriction = data['Data_Access_Restriction']
             access_rights = ''
             access_rightsURI = ''
             if access_restriction:
                 if access_restriction.startswith('Open'):
                     access_rights = 'unrestricted' #'Open Access'
                     access_rightsURI = 'info:eu-repo/semantics/openAccess'
                 elif access_restriction.startswith('Restricted'):
                     access_rights = 'restricted' #'Restricted Access'
                     access_rightsURI = 'info:eu-repo/semantics/restrictedAccess'
                 elif access_restriction.startswith('Closed'):
                     access_rights = 'private' #'Closed Access'
                     access_rightsURI = 'info:eu-repo/semantics/closedAccess'

             resourceConstraints = GMD.resourceConstraints()
             MD_LegalConstraints = GMD.MD_LegalConstraints()
             accessConstraints = GMD.accessConstraints()

             MD_RestrictionCode = GMD.MD_RestrictionCode()
             MD_RestrictionCode.attrib['codeList'] = 'http://www.isotc211.org/2005/resources/codeList.xml#MD_RestrictionCode'
             MD_RestrictionCode.attrib['codeListValue'] = access_rights

             accessConstraints.append(MD_RestrictionCode)
             otherConstraints = GMD.otherConstraints()
             otherConstraints.append(GCO.CharacterString(license))
             accessConstraints.append(otherConstraints)

             MD_LegalConstraints.append(accessConstraints)
             resourceConstraints.append(MD_LegalConstraints)
             MD_DataIdentification.append(resourceConstraints)

         except (IndexError, KeyError) as e:
             pass


# Related datapackages, References, cites, IsSupplementTo

         # Related identifiers
         try:
             for identifier in data['Related_Datapackage']:
                 aggregationInfo = GMD.aggregationInfo()
                 MD_AggregateInformation = GMD.MD_AggregateInformation()
                 aggregateDataSetIdentifier = GMD.aggregateDataSetIdentifier()
                 RS_Identifier = GMD.RS_Identifier()

                 code = GMD.code()
                 code.append(GCO.CharacterString(identifier['Persistent_Identifier']['Identifier']))
                 RS_Identifier.append(code)

                 codeSpace = GMD.codeSpace()
                 codeSpace.append(GCO.CharacterString(identifier['Persistent_Identifier']['Identifier_Scheme']))

                 RS_Identifier.append(codeSpace)
                 aggregateDataSetIdentifier.append(RS_Identifier)
                 MD_AggregateInformation.append(aggregateDataSetIdentifier)

                 relation_type = identifier['Relation_Type'].split(':')[0]
                 DS_AssociationTypeCode = GMD.DS_AssociationTypeCode(relation_type)
                 DS_AssociationTypeCode.attrib['codeList'] = 'http://datacite.org/schema/kernel-4'
                 DS_AssociationTypeCode.attrib['codeListValue'] = relation_type

                 associationType = GMD.associationType()
                 associationType.append(DS_AssociationTypeCode)
                 MD_AggregateInformation.append(associationType)

                 aggregationInfo.append(MD_AggregateInformation)

                 #Add each related identifier
                 MD_DataIdentification.append(aggregationInfo)
         except KeyError:
             pass



# LANGUAGE - defined higher in hierarchy as well
         # Language
         language = GMD.language()
         language.append(GCO.CharacterString(languageVal))

         MD_DataIdentification.append(language)



# GEO LOCATION INFO
         # GeoLocation
         try:
             extent = GMD.extent()
             location_present = False
             for geoloc in data['GeoLocation']:
                 EX_Extent = GMD.EX_Extent()

                 location_present = True
                 temp_description_start = geoloc['Description_Temporal']['Start_Date']
                 temp_description_end = geoloc['Description_Temporal']['End_Date']
                 spatial_description = geoloc['Description_Spatial']

                 lon0 = str(geoloc['geoLocationBox']['westBoundLongitude'])
                 lat0 = str(geoloc['geoLocationBox']['northBoundLatitude'])
                 lon1 = str(geoloc['geoLocationBox']['eastBoundLongitude'])
                 lat1 = str(geoloc['geoLocationBox']['southBoundLatitude'])

                 if spatial_description:
                     description = GMD.description()
                     description.append(GCO.CharacterString(spatial_description))
                     EX_Extent.append(description)

                 geographicElement = GMD.geographicElement() # only one per cycle

                 if lon0==lon1 and lat0==lat1: # dealing with a point, nog uitzoeken ISO
                     EX_GeographicBoundingBox = GMD.EX_GeographicBoundingBox()
                     #geoLocationPoint = GMD.geoLocationPoint()
                     #geoLocationPoint.append(GMD.pointLongitude(lon0))
                     #geoLocationPoint.append(GMD.pointLatitude(lat0))
                     #geoLocation.append(geoLocationPoint)
                     EX_Extent.append(EX_GeographicBoundingBox)
                 else:
                     EX_GeographicBoundingBox = GMD.EX_GeographicBoundingBox()

                     westBoundLongitude = GMD.westBoundLongitude()
                     westBoundLongitude.append(GCO.Decimal(lon0))
                     eastBoundLongitude = GMD.eastBoundLongitude()
                     eastBoundLongitude.append(GCO.Decimal(lon1))

                     southBoundLatitude = GMD.southBoundLatitude()
                     southBoundLatitude.append(GCO.Decimal(lat0))
                     northBoundLatitude = GMD.northBoundLatitude()
                     northBoundLatitude.append(GCO.Decimal(lat1))

                     EX_GeographicBoundingBox.append(westBoundLongitude)
                     EX_GeographicBoundingBox.append(eastBoundLongitude)
                     EX_GeographicBoundingBox.append(southBoundLatitude)
                     EX_GeographicBoundingBox.append(northBoundLatitude)
                     EX_Extent.append(EX_GeographicBoundingBox)

                 extent.append(EX_Extent)

             # alleen toevoegen als er werkelijk locaties zijn
             if location_present:
                 MD_DataIdentification.append(extent)

         except (IndexError, KeyError) as e:
             pass


         identificationInfo.append(MD_DataIdentification)
         iso.append(identificationInfo)
         element.append(iso)

         return

###############################################################################################################

'''

# Contributors - ook weer Responsible parties!


   Contributor types:   -> will all default in ISO role 'contributor' for now.
        "ContactPerson",
        "DataCollector",
        "DataCurator",
        "DataManager",
        "Distributor",
        "Editor",
        "HostingInstitution",
        "Producer",
        "ProjectLeader",
        "ProjectManager",
        "ProjectMember",
        "RegistrationAgency",
        "RegistrationAuthority",
        "RelatedPerson",
        "Researcher",
        "ResearchGroup",
        "RightsHolder",
        "Sponsor",
        "Supervisor",
        "WorkPackageLeader"
'''



'''
         # ResourceType # DATACITE specifiek! Hoe dit in ISO onderbrengen!!!???

         # List as defined by Ton/Maarten/Frans 20190603
         dictResourceTypes = {'Dataset'  : 'Research Data',
                              'DataPaper': 'Method Description',
                              'Software' : 'Computer Code',
                              'Text'     : 'Other Document'}

         try:
             resourceTypeGeneral = data['Data_Type']
             resourceTypeLabel = dictResourceTypes[resourceTypeGeneral]
             resourceType = GMD.resourceType(resourceTypeLabel)
             resourceType.attrib['resourceTypeGeneral'] = resourceTypeGeneral
             datacite.append(resourceType)
         except KeyError:
	     resourceType = GMD.resourceType('Other Document')
             resourceType.attrib['resourceTypeGeneral'] = 'Text'
             datacite.append(resourceType)
             pass
'''


'''
         # Version  ## HOE DIT IN ISO te vatten!?
         try:
             datacite.append(GMD.version(data['Version']))
         except KeyError:
             pass

'''
