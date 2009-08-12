
from lxml.builder import ElementMaker
import simplejson

from moai import MetaDataFormat, name
from moai.meta import METADATA_FORMATS

XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

class OAIDC(MetaDataFormat):
    """The standard OAI Dublin Core metadata format.
    
    Every OAI feed should at least provide this format.

    It is registered under the name 'oai_dc'
    """
    
    name('oai_dc')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                   'dc':'http://purl.org/dc/elements/1.1/'}
        self.schemas = {'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd'}
        
    def __call__(self, element, metadata):

        data = metadata.record
        
        OAI_DC =  ElementMaker(namespace=self.ns['oai_dc'],
                               nsmap =self.ns)
        DC = ElementMaker(namespace=self.ns['dc'])

        oai_dc = OAI_DC.dc()
        oai_dc.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
            self.ns['oai_dc'],
            self.schemas['oai_dc'])

        for field in ['title', 'creator', 'subject', 'description',
                      'publisher', 'contributor', 'type', 'format',
                      'identifier', 'source', 'language', 'date',
                      'relation', 'coverage', 'rights']:
            el = getattr(DC, field)
            for value in data['metadata'].get(field, []):
                if field == 'identifier' and data['metadata'].get('url'):
                    value = data['metadata']['url'][0]
                oai_dc.append(el(value))
        
        element.append(oai_dc)

class MODS(MetaDataFormat):
    """This is the minimods formats as defined by DARE.

    It is registered as prefix 'mods'.'
    """
    
    name('mods')
    
    def __init__(self, prefix, config, db):
        self.prefix = prefix
        self.config = config
        self.db = db

        self.ns = {'mods': 'http://www.loc.gov/mods/v3',
                   'xml':'http://www.w3.org/XML/1998/namespace',
                   'dai': 'info:eu-repo/dai'}

        self.schemas = {
           'mods': 'http://www.loc.gov/standards/mods/v3/mods-3-2.xsd'}
        
    def __call__(self, element, metadata):

        data = metadata.record
        MODS = ElementMaker(namespace=self.ns['mods'], nsmap=self.ns)
        DAI = ElementMaker(namespace=self.ns['dai'], nsmap=self.ns)
        mods = MODS.mods(version="3.2")

        if data['metadata'].get('identifier'):
            mods.append(MODS.identifier(data['metadata']['identifier'][0],
                                        type="uri"))

        if data['metadata'].get('url'):
            mods.append(MODS.location(MODS.url(data['metadata']['url'][0])))

        if data['metadata'].get('title'):
            titleInfo = MODS.titleInfo(
                MODS.title(data['metadata']['title'][0])
                )
            titleInfo.attrib['{%s}lang' % self.ns['xml']] = data['metadata'].get(
                'language', ['en'])[0]
            mods.append(titleInfo)
            
        if data['metadata'].get('description'):
            mods.append(MODS.abstract(data['metadata']['description'][0]))


        for ctype in ['author', 'editor', 'advisor']:
            contributor_data = []
            for id in data['metadata'].get('%s_rel' % ctype, []):
                contributor = self.db.get_metadata(id)
                contributor['id'] = id
                contributor_data.append(contributor)

            if data['metadata'].get('%s_data' % ctype):
                contributor_data = [simplejson.loads(s) for s in data[
                    'metadata']['%s_data' % ctype]]
        
            if not contributor_data:            
                contributor_data = [{'name':[a]} for a in data[
                    'metadata'].get(ctype, [])]

            dai_list = []
            for contributor in contributor_data:
                unique_id = data['record']['id'] + '_' + contributor.get(
                    'id', contributor['name'][0])
                if unique_id[0].isdigit():
                    unique_id = '_'+unique_id
                unique_id = unique_id.replace(':', '')
                name = MODS.name(
                    MODS.displayForm(contributor['name'][0]),
                    type='personal',
                    id=unique_id
                    )
                surname = contributor.get('surname')
                if surname:
                    name.append(MODS.namePart(surname[0], type="family"))
                firstname = contributor.get('firstname')
                if firstname:
                    name.append(MODS.namePart(firstname[0], type="given"))

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
                for id, dai in dai_list:
                    daiList.append(DAI.identifier(
                        dai[0],
                        IDRef=id,
                        authority='info:eu-repo/dai/nl'))
                
                mods.append(MODS.extension(daiList))


        dgg = data['metadata'].get('degree_grantor')
        if dgg:
            mods.append(MODS.name(
                MODS.namePart(dgg[0]),
                MODS.role(
                  MODS.roleTerm('dgg',
                                authority="marcrelator",
                                type="code")
                ),
                type="corporate"))

        if data['metadata'].get('language'):
            mods.append(MODS.language(
                MODS.languageTerm(data['metadata']['language'][0],
                                  type="code",
                                  authority="rfc3066")))

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
                    MODS.identifier('urn:issn:%s' % issn[0],
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
                                        encoding='iso8601'))

        mods.append(MODS.typeOfResource('text'))        
        if data['metadata'].get('dare_type'):
            mods.append(MODS.genre(data['metadata']['dare_type'][0]))

        
        classifications = data['metadata'].get('classification', [])
        for classification in data['metadata'].get('classification', []):
            if classification.count('#') == 1:
                authority, value = classification.split('#')
                mods.append(MODS.classification(value, authority=authority))
            else:
                mods.append(MODS.classification(classsification))
        
        subjects = data['metadata'].get('subject', [])
        if subjects:
            s_el = MODS.subject()
            for subject in subjects:
                s_el.append(MODS.topic(subject))
            mods.append(s_el)

        if data['metadata'].get('rights'):
            mods.append(MODS.accessCondition(data['metadata']['rights'][0]))
        
            
        mods.attrib['{%s}schemaLocation' % XSI_NS] = '%s %s' % (
            self.ns['mods'],
            self.schemas['mods'])
        
        element.append(mods)

