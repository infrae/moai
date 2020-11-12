
from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

class OAIDC(object):
    """The standard OAI Dublin Core metadata format.

    Every OAI feed should at least provide this format.

    It is registered under the name 'oai_dc'
    """

    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                   'dc':'http://purl.org/dc/elements/1.1/'}
        self.schemas = {
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'}

    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]

    def __call__(self, element, metadata):

        #data = metadata.record
        data = metadata.record['metadata']['metadata']

        OAI_DC =  ElementMaker(namespace=self.ns['oai_dc'],
                               nsmap =self.ns)
        DC = ElementMaker(namespace=self.ns['dc'])

        oai_dc = OAI_DC.dc()
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
            self.ns['oai_dc'],
            self.schemas['oai_dc'])

# Title
        try:
            oai_dc.append(DC.title(data['Title']))
        except (IndexError,KeyError) as e:
            pass

# Creator
        try:
            creator_list = data['Creator']
            if isinstance(creator_list, list)==False:
                creator_list = [creator_list]

            for dccreator in creator_list:
                name = dccreator['Name']['Given_Name'] + ' ' +  dccreator['Name']['Family_Name']

                affiliation_list = dccreator['Affiliation']
                if isinstance(affiliation_list, list)==False:
                    affiliation_list = [affiliation_list]

                # Compile creatorData
                creatorData = name + ' (' + ', '.join(affiliation_list)  + ')'
                oai_dc.append(DC.creator(creatorData))
        except (IndexError,KeyError) as e:
            pass


# Subject  - collection of Disciplines / tags etc
        try:
            # Disciplines and Tags
            list_subjects = data['Discipline'] +  data['Tag']
            if isinstance(list_subjects, list)==False:
                list_subjects = [list_subjects]
            for subject in list_subjects:
                if len(subject):
		    oai_dc.append(DC.subject(subject))

            # ILAB specific - collection name
            try:
                oai_dc.append(DC.subject(data['Collection_Name']))
            except (IndexError,KeyError) as e:
                pass

            # GEO specific
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
                            oai_dc.append(DC.subject(subject))
                except (IndexError,KeyError) as e:
                    continue

        except (IndexError,KeyError) as e:
            pass

# Description
        try:
            oai_dc.append(DC.description(data['Description']))
        except (IndexError,KeyError) as e:
            pass

# Publisher
        try:
            oai_dc.append(DC.publisher('Utrecht University'))
        except (IndexError,KeyError) as e:
            pass

# Contributor
        try:
            con_list = data['Contributor']
            if isinstance(con_list, list)==False:
                con_list = [con_list]

            for dccon in creator_list:
                name = dccon['Name']['Given_Name'] + ' ' +  dccon['Name']['Family_Name']

                affiliation_list = dccon['Affiliation']
                if isinstance(affiliation_list, list)==False:
                    affiliation_list = [affiliation_list]

                # Compile creatorData
                conData = name + ' (' + ', '.join(affiliation_list)  + ')'
                oai_dc.append(DC.contributor(conData))
        except (IndexError,KeyError) as e:
            pass

# Identifier
        try:
            doi = data['System']['Persistent_Identifier_Datapackage']['Identifier']
            oai_dc.append(DC.identifier('doi:' + doi))
        except (IndexError,KeyError) as e:
            pass

# Language
        try:
            oai_dc.append(DC.language(data['Language']))
        except (IndexError,KeyError) as e:
            pass

# Date
        try:
            oai_dc.append(DC.date(data['System']['Publication_Date']))
        except (IndexError,KeyError) as e:
            pass

# COVERAGE
        # Default metadata schema
        try:
            text_locations = data['Covered_Geolocation_Place']
            for location in text_locations:
                oai_dc.append(DC.coverage(location))
        except (IndexError,KeyError) as e:
            pass

        try:
            perioddates = [data['Covered_Period/Start_Date'], data['Covered_Period/End_Date']]
            period = "/".join([d for d in perioddates if d])
            oai_dc.append(DC.coverage(period))
        except (IndexError,KeyError) as e:
            pass


        # GEO schemas
        try:
            #GEO schemas hold combination of geobox/text/date range
            for geoloc in data['GeoLocation']:
                location_present = True
                temp_description_start = geoloc['Description_Temporal']['Start_Date']
                temp_description_end = geoloc['Description_Temporal']['End_Date']
                spatial_description = geoloc['Description_Spatial']

                lon0 = str(geoloc['geoLocationBox']['westBoundLongitude'])
                lat0 = str(geoloc['geoLocationBox']['northBoundLatitude'])
                lon1 = str(geoloc['geoLocationBox']['eastBoundLongitude'])
                lat1 = str(geoloc['geoLocationBox']['southBoundLatitude'])

                geoData = '(' + lat0 + ' ,' + lon0 + ') (' + lat1 + ', ' + lon1 + ')'

                if spatial_description:
                    geoData += ' | ' + spatial_description

                if temp_description_start:
                    geoData += ' | ' + temp_description_start

                if temp_description_end:
                    geoData += ' | ' + temp_description_end

                oai_dc.append(DC.coverage(geoData))

        except (IndexError,KeyError) as e:
            pass

# Rights
        try:
            license = data['License']
            rightLicenseURL = data['System']['License_URI']

            accessRestriction = data['Data_Access_Restriction']
            if accessRestriction.startswith('Open'):
                accessRights = 'Open Access'
                accessRightsURI = 'info:eu-repo/semantics/openAccess'
            elif accessRestriction.startswith('Restricted'):
                accessRights = 'Restricted Access'
                accessRightsURI = 'info:eu-repo/semantics/restrictedAccess'
            elif accessRestriction.startswith('Closed'):
                accessRights = 'Closed Access'
                accessRightsURI = 'info:eu-repo/semantics/closedAccess'

            rights = license + ' (' + rightLicenseURL + ')'
            rights += ' | ' + accessRights + ' (' + accessRightsURI + ')'

            oai_dc.append(DC.rights(rights))

        except (IndexError,KeyError) as e:
            pass

        element.append(oai_dc)
