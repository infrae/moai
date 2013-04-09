import re
import uuid

from lxml.builder import ElementMaker

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

class MODS(object):
    """This is the minimods formats as defined by DARE.

    It is registered as prefix 'mods'.'
    """
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'mods': 'http://www.loc.gov/mods/v3',
                   'xml':'http://www.w3.org/XML/1998/namespace',
                   'dai': 'info:eu-repo/dai',
                   'gal': 'info:eu-repo/grantAgreement'}

        self.schemas = {
           'mods': 'http://www.loc.gov/standards/mods/v3/mods-3-3.xsd',
           'dai': 'http://purl.org/REP/standards/dai-extension.xsd',
           'gal': 'http://purl.org/REP/standards/gal-extension.xsd'}
        
        
    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]
    
    def __call__(self, element, metadata):

        data = metadata.record
        MODS = ElementMaker(namespace=self.ns['mods'], nsmap=self.ns)
        DAI = ElementMaker(namespace=self.ns['dai'], nsmap=self.ns)
        GAL = ElementMaker(namespace=self.ns['gal'], nsmap=self.ns)
        mods = MODS.mods(version="3.3")
        if data['metadata'].get('identifier'):
            mods.append(MODS.identifier(data['metadata']['identifier'][0],
                                        type="uri"))
        for key, value in data['metadata'].get('identifier_data', {}).items():
            mods.append(MODS.identifier(value, type=key))
                
            
        if data['metadata'].get('title'):
            titleInfo = MODS.titleInfo(
                MODS.title(data['metadata']['title'][0])
                )
            titleInfo.attrib['{%s}lang' % self.ns['xml']] = data['metadata'].get(
                'language', ['en'])[0]
            mods.append(titleInfo)

        mods.append(MODS.typeOfResource('text'))        
        if data['metadata'].get('dare_type'):
            mods.append(MODS.genre(data['metadata']['dare_type'][0]))

        if data['metadata'].get('url'):
            location_el = MODS.location(MODS.url(data['metadata']['url'][0],
                                                 usage="primary display",
                                                 access="object in context"))
            for asset in data['metadata'].get('asset', []):
                if asset.get('access') == 'open':
                    location_el.append(MODS.url(asset['absolute_uri'],
                                                access='raw object'))
            mods.append(location_el)

        public_assets = [a for a in data['metadata'].get('asset', [])
                         if a.get('access') == 'open']
        if len(public_assets) == 1:
            phys_descr_el = MODS.physicalDescription()
            if asset.get('mimetype'):
                phys_descr_el.append(MODS.internetMediaType(asset['mimetype']))
            if asset.get('bytes'):
                try:
                    kbytes = re.sub(r'(\d{3})(?=\d)', r'\1,',
                                    str(int(asset['bytes'])/1024)[::-1])[::-1]
                
                    phys_descr_el.append(MODS.extent('Filesize: %s KB' % kbytes))
                except:
                    pass
                
            phys_descr_el.append(MODS.digitalOrigin('born digital'))
            mods.append(phys_descr_el)
            
            
        if data['metadata'].get('description'):
            mods.append(MODS.abstract(data['metadata']['description'][0]))


        for ctype in ['author', 'editor', 'advisor']:
            contributor_data = []
            for id in data['metadata'].get('%s_rel' % ctype, []):
                contributor = self.db.get_metadata(id)
                contributor['id'] = id
                contributor_data.append(contributor)

            if data['metadata'].get('%s_data' % ctype):
                contributor_data = [s for s in data['metadata'][
                    '%s_data' % ctype]]
        
            if not contributor_data:            
                contributor_data = [{'name':[a]} for a in data[
                    'metadata'].get(ctype, [])]

            dai_list = []
            for contributor in contributor_data:
                contributor_name = contributor.get('name', [''])[0]
                unique_id = uuid.uuid4().hex
                if unique_id[0].isdigit():
                    unique_id = '_'+unique_id
                name = MODS.name(
                    MODS.displayForm(contributor_name),
                    type='personal',
                    ID=unique_id
                    )
                surname = contributor.get('surname')
                if surname:
                    surname = surname[0]
                    prefix = contributor.get('prefix')
                    if prefix:
                        surname = u'%s, %s' % (surname, prefix[0])
                    name.append(MODS.namePart(surname, type="family"))
                initials = contributor.get('initials')
                firstname = contributor.get('firstname')
                if firstname:
                    name.append(MODS.namePart(firstname[0], type="given"))
                elif initials:
                    name.append(MODS.namePart(initials[0], type="given"))
                    
                role = contributor.get('role')
                if role:
                    role = role[0]
                else:
                    roles = {'author': 'aut', 'editor': 'edt', 'advisor':'ths'}
                    role = roles[ctype]
                name.append(                    
                    MODS.role(
                    MODS.roleTerm(role,
                                  type='code',
                                  authority='marcrelator')
                    ))
                mods.append(name)
                dai = contributor.get('dai')
                if dai:
                    dai_list.append((unique_id, dai))
            if dai_list:
                daiList = DAI.daiList()
                daiList.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
                    self.ns['dai'],
                    self.schemas['dai'])

                for id, dai in dai_list:
                    daiList.append(DAI.identifier(
                        dai[0].split('/')[-1],
                        IDref=id,
                        authority='info:eu-repo/dai/nl'))
                
                mods.append(MODS.extension(daiList))

        for corp in data['metadata'].get('corporate_data', []):
            roles = MODS.role()
            if corp.get('role'):
                roles.append(MODS.roleTerm(corp['role'],
                                           authority="marcrelator",
                                           type="text"))
            if corp.get('role_code'):
                roles.append(MODS.roleTerm(corp['role_code'],
                                           authority="marcrelator",
                                           type="code"))
            mods.append(MODS.name(
                MODS.namePart(corp['name']),
                roles,
                type="corporate"))
            
        if data['metadata'].get('language'):
            lang_el = MODS.language(
                MODS.languageTerm(data['metadata']['language'][0],
                                  type="code",
                                  authority="rfc3066"))
            if data['metadata']['language'][0] == 'en':
                lang_el.append(MODS.languageTerm('English', type="text"))
            if data['metadata']['language'][0] == 'nl':
                lang_el.append(MODS.languageTerm('Nederlands', type="text"))
            mods.append(lang_el)
            
        for host in ['journal', 'series']:
            title = data['metadata'].get('%s_title' % host)
            part_type = {'journal': 'host'}.get(host, host)
            relitem = MODS.relatedItem(type=part_type)
            if title:
                relitem.append(MODS.titleInfo(MODS.title(title[0])))
            else:
                continue
            issn = data['metadata'].get('%s_issn' % host)
            if issn:
                relitem.append(
                    MODS.identifier(issn[0],
                                    type="issn"))
            host_uri = data['metadata'].get('%s_uri' % host)
            if host_uri:
                relitem.append(
                    MODS.identifier(host_uri[0],
                                    type="uri"))
            volume = data['metadata'].get('%s_volume' % host)
            issue = data['metadata'].get('%s_issue' % host)
            start_page = data['metadata'].get('%s_start_page' % host)
            end_page = data['metadata'].get('%s_end_page' % host)
            if volume or issue or end_page or start_page:
                part = MODS.part()
                if volume:
                    part.append(MODS.detail(MODS.number(volume[0]),
                                            type="volume"))
                if issue:
                    part.append(MODS.detail(MODS.number(issue[0]),
                                            type="issue"))
                if start_page or end_page:
                    extent = MODS.extent(unit="page")
                    if start_page:
                        extent.append(MODS.start(start_page[0]))
                    if end_page:
                        extent.append(MODS.end(end_page[0]))
                    part.append(extent)
                relitem.append(part)
            if data['metadata'].get('%s_publisher' % host):
                relitem.append(
                    MODS.originInfo(
                      MODS.publisher(
                        data['metadata']['%s_publisher' % host][0])))
                
            mods.append(relitem)

        origin = MODS.originInfo()
        mods.append(origin)
        if data['metadata'].get('publisher'):
            origin.append(MODS.publisher(data['metadata']['publisher'][0]))
        if data['metadata'].get('date'):
            origin.append(MODS.dateIssued(data['metadata']['date'][0],
                                        encoding='w3cdtf'))

        
        classifications = data['metadata'].get('classification', [])
        for classification in classifications:
            if classification.count('#') == 1:
                authority, value = classification.split('#')
                mods.append(MODS.classification(value, authority=authority))
            else:
                mods.append(MODS.classification(classification))
        
        subjects = data['metadata'].get('subject', [])
        if subjects:
            s_el = MODS.subject()
            for subject in subjects:
                s_el.append(MODS.topic(subject))
            mods.append(s_el)

        if data['metadata'].get('rights'):
            mods.append(MODS.accessCondition(data['metadata']['rights'][0]))
        
        projects = data['metadata'].get('project', [])
        funders = set([prj['funder'] for prj in projects if prj.get('funder')])
        funder_ids = {}
        for funder in funders:
            unique_id = uuid.uuid4().hex
            if unique_id[0].isdigit():
                unique_id = '_'+unique_id
            funder_ids[funder] = unique_id
            mods.append(
                MODS.name(MODS.namePart(funder),
                          MODS.role(MODS.roleTerm('fnd',
                                                  authority='marcrelator',
                                                  type='code')),
                          ID=unique_id,
                          type='corporate'))
        
        if projects:
            galList = GAL.grantAgreementList()
            galList.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
                self.ns['gal'],
                self.schemas['gal'])
            mods.append(MODS.extension(galList))
            for prj in projects:
                el = GAL.grantAgreement(code=prj['id'])
                if prj.get('funder'):
                    el.append(GAL.funder(IDref=funder_ids[prj['funder']]))
                if prj.get('title'):
                    el.append(GAL.title(prj['title']))
                galList.append(el)

        info = data['metadata'].get('record_info_data', {})
        if info:
            record_info_el = MODS.recordInfo()
            if info.get('source'):
                record_info_el.append(MODS.recordContentSource(info['source']))
            if info.get('identifier'):
                record_info_el.append(MODS.recordIdentifier(info['identifier']))
            for key, value in info.get('identifier_data', {}).items():
                record_info_el.append(MODS.recordIdentifier(value, source=key))
            if info.get('origin'):
                record_info_el.append(MODS.recordOrigin(info['origin']))
            if info.get('created'):
                record_info_el.append(
                    MODS.recordCreationDate(info['created'],
                                            encoding="w3cdtf"))
            if info.get('changed'):
                record_info_el.append(
                    MODS.recordChangeDate(info['changed'],
                                          encoding="w3cdtf"))
            mods.append(record_info_el)
            
        mods.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
            self.ns['mods'],
            self.schemas['mods'])
        
        element.append(mods)

class NL_MODS(MODS):
    """
    like mods, but dateIssued uses wrong iso8601 encoding instead of w3cdtf
    """
    def __init__(self, prefix, config, db):
        super(NL_MODS, self).__init__(prefix, config, db)
        self.ns['nl_mods'] = self.ns['mods']
        self.schemas['nl_mods'] = self.schemas['mods']
        
    def __call__(self, element, metadata):
        super(NL_MODS, self).__call__(element, metadata)
        for el in element.xpath(
            './mods:mods/mods:originInfo/'
            'mods:dateIssued[@encoding="w3cdtf"]', namespaces=self.ns):
            el.attrib['encoding'] = 'iso8601'
        
        
