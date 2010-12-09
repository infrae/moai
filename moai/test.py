# coding=utf8
import os
from unittest import TestCase, TestSuite, makeSuite
import doctest
import datetime
import urllib2

from lxml import etree
import wsgi_intercept
from wsgi_intercept.urllib2_intercept import install_opener

from moai.utils import XPath
from moai.database import Database
from moai.server import Server, FeedConfig
from moai.wsgi import MOAIWSGIApp
from moai.provider.file import FileBasedContentProvider
from moai.example import ExampleContent
install_opener()

FLAGS = doctest.NORMALIZE_WHITESPACE + doctest.ELLIPSIS
GLOBS = {}

class XPathUtilTest(TestCase):

    def test_string(self):
        doc = etree.fromstring(
            '''<doc>
                 <string>test</string>
                 <string/>
                 <string>   test     </string>
                 <string>test<foo/>more test</string>
                 <string>tëst</string>
               </doc>''')
        xpath = XPath(doc)
        self.assertEquals(xpath.strings('/doc/string'),
                          [u'test', u'test', u'test', u'tëst'])
    def test_boolean(self):
        doc = etree.fromstring(
            '''<doc>
                 <bool>yes</bool>
                 <bool>true</bool>
                 <bool>False</bool>
                 <bool>NO</bool>
               </doc>''')
        xpath = XPath(doc)
        self.assertEquals(xpath.booleans('/doc/bool'),
                          [True, True, False, False])

    def test_number(self):
        doc = etree.fromstring(
            '''<doc>
                 <number>1</number>
                 <number>3.33333333333</number>
                 <number>-75</number>
                 <number>-0.75</number>
               </doc>''')
        xpath = XPath(doc)
        numbers = xpath.numbers('/doc/number')
        self.assertEquals(numbers,
                          [1, 3.33333333333, -75, -0.75])
        self.assertEquals([type(i) for i in numbers],
                          [int, float, int, float])

        
    def test_date(self):
        doc = etree.fromstring(
            '''<doc>
                 <date>2010-01-04</date>
                 <date>2010/01/04</date>
                 <date>2010-01-04T12:43:33Z</date>
                 <date>2010-01-04T12:43:33</date>
               </doc>''')
        xpath = XPath(doc)
        self.assertEquals(xpath.dates('/doc/date'),
                          [datetime.datetime(2010, 1, 4, 0, 0),
                           datetime.datetime(2010, 1, 4, 0, 0),
                           datetime.datetime(2010, 1, 4, 12, 43, 33),
                           datetime.datetime(2010, 1, 4, 12, 43, 33)])

    def test_tags(self):
        doc = etree.fromstring('<doc><a/><b/><s:c xmlns:s="urn:spam"/></doc>')
        xpath = XPath(doc)
        self.assertEquals(xpath.tags('/doc/*'), [u'a', u'b', u'c'])

    def test_namespaces(self):
        doc = etree.fromstring(
            '<doc xmlns="urn:spam"><string>Spam!</string></doc>')
        xpath = XPath(doc, nsmap={'spam': 'urn:spam'})
        self.assertEquals(xpath.string('//spam:string'), u'Spam!')

class DatabaseTest(TestCase):
    def setUp(self):
        self.db = Database()
        
    def tearDown(self):
        del self.db
        
    def test_update(self):
        # db is empty
        self.assertEquals(self.db.record_count(), 0)
        # let's add a record
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {},
                              {u'title': u'Spam!'})
        self.db.flush()
        self.assertEquals(self.db.record_count(), 1)
        # check if all values are there
        record = self.db.get_record(u'oai:spam')
        self.assertEquals(record['id'], u'oai:spam')
        self.assertEquals(record['deleted'], False)
        self.assertEquals(record['modified'],
                          datetime.datetime(2010, 10, 13, 12, 30, 00))
        self.assertEquals(record['sets'], [])
        self.assertEquals(record['metadata'], {u'title': u'Spam!'})
        # change a metadata value
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 01),
                              False,
                              {},
                              {u'title': u'Ham!'})
        self.db.flush()
        self.assertEquals(self.db.record_count(), 1)
        # check if metadata was changed
        record = self.db.get_record(u'oai:spam')
        self.assertEquals(record['metadata'], {u'title': u'Ham!'})
        # remove the record
        self.db.remove_record(u'oai:spam')
        self.assertEquals(self.db.record_count(), 0)
        
    def test_setrefs(self):
        # add a record that references a set
        self.assertEquals(self.db.set_count(), 0)
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {u'spamset': {u'name': u'Spam Set',
                                            u'description': u'spam spam spam',
                                            u'hidden': False}},
                              {u'title': u'Spam!'})
        self.db.flush()
        self.assertEquals(self.db.record_count(), 1)
        self.assertEquals(self.db.set_count(), 1)
        # check if all values are there
        record = self.db.get_record(u'oai:spam')
        self.assertEquals(record['sets'], [u'spamset'])
        set = self.db.get_set(u'spamset')
        self.assertEquals(set['id'], u'spamset')
        self.assertEquals(set['name'], u'Spam Set')
        self.assertEquals(set['description'], u'spam spam spam')
        self.assertEquals(set['hidden'], False)
        # now, we'll change the record to use the hamset
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {u'hamset': {u'name': u'Ham Set',
                                            u'description': u'ham ham ham',
                                            u'hidden': False}},
                              {u'title': u'Ham!'})
        self.db.flush()
        self.assertEquals(self.db.record_count(), 1)
        # note that we now have 2 sets, the spam set is not removed
        self.assertEquals(self.db.set_count(), 2)
        # however, the spam record only has one reference 
        record = self.db.get_record(u'oai:spam')
        self.assertEquals(record['sets'], [u'hamset'])
        # if the set is removed then all references to that set are
        # also removed
        self.db.remove_set(u'hamset')
        record = self.db.get_record(u'oai:spam')
        self.assertEquals(record['sets'], [])
        self.assertEquals(self.db.set_count(), 1)

    def test_hidden_sets(self):
        # hidden sets are not added to the record setrefs list,
        # they are there though, for filtering purposes
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {u'spamset': {u'name': u'Spam Set',
                                            u'description': u'spam spam spam',
                                            u'hidden': False},
                               u'hamset': {u'name': u'Ham Set',
                                           u'description': u'ham ham ham',
                                           u'hidden': True}},
                              {u'title': u'Spam!'})
        self.db.flush()
        self.assertEquals(self.db.get_setrefs(u'oai:spam'), [u'spamset'])
        self.assertEquals(self.db.get_setrefs(u'oai:spam',
                                              include_hidden_sets=True),
                          [u'hamset', u'spamset'])
        # hidden sets are also never shown in the oai sets listing
        self.assertEquals(list(self.db.oai_sets()),
                          [{'description': u'spam spam spam',
                            'id': u'spamset',
                            'name': u'Spam Set'}] )

    def test_earliest_datestamp(self):
        self.assertEquals(self.db.oai_earliest_datestamp(),
                          datetime.datetime(1970, 1, 1, 0, 0))
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {}, {})
        self.db.update_record(u'oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {}, {})
        self.db.flush()
        self.assertEquals(self.db.oai_earliest_datestamp(),
                          datetime.datetime(2009, 10, 13, 12, 30))

    def test_oai_query_dates(self):
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 01, 01, 00, 00, 00),
                              False, {u'spamset':{u'name':u'spam'}},
                              {})
        self.db.update_record(u'oai:ham',
                              datetime.datetime(2009, 01, 01, 00, 00, 00),
                              False, {u'hamset':{u'name':u'ham'}},
                              {})
        self.db.flush()
        self.assertEquals(
            list(self.db.oai_query()),
            [{'deleted': False,
              'sets': [u'spamset'],
              'metadata': {},
              'id': u'oai:spam',
              'modified': datetime.datetime(2010, 1, 1, 0, 0)},
             {'deleted': False,
              'sets': [u'hamset'],
              'metadata': {},
              'id': u'oai:ham',
              'modified': datetime.datetime(2009, 1, 1, 0, 0)}])
        # date slices
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            from_date=datetime.datetime(2009, 6, 1, 0, 0))],
            [u'oai:spam'])
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            until_date=datetime.datetime(2009, 6, 1, 0, 0))],
            [u'oai:ham'])
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            from_date=datetime.datetime(2008, 6, 1, 0, 0),
            until_date=datetime.datetime(2010, 6, 1, 0, 0))],
            [u'oai:spam', u'oai:ham'])
        # no matches
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            from_date=datetime.datetime(2011, 1, 1, 0, 0))],
            [])
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            until_date=datetime.datetime(2008, 1, 1, 0, 0))],
            [])
        # test inclusiveness
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(
            from_date=datetime.datetime(2009, 1, 1, 0, 0),
            )],
            [u'oai:spam', u'oai:ham'])

    def test_oai_query_identifier(self):
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2010, 01, 01, 00, 00, 00),
                              False, {u'spamset':{u'name':u'spam'}},
                              {})
        self.db.flush()
        self.assertEquals(
            [r['id'] for r in self.db.oai_query(identifier=u'oai:spam')],
            [u'oai:spam'])
        
    def test_oai_query_future_dates(self):
        # records with a timestamp in the future should never
        # be returned, this feature can be used to create embargo dates
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2020, 01, 01, 00, 00, 00),
                              False, {u'spamset':{u'name':u'spam'}},
                              {})
        self.db.flush()
        self.assertEquals(list(self.db.oai_query()), [])
        self.assertEquals(list(self.db.oai_query(
            until_date=datetime.datetime(2030, 01, 01, 00, 00, 00))), [])
        self.assertEquals(list(self.db.oai_query(identifier=u'oai:spam')), [])
        
    def test_oai_sets(self):
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset'),
                                      u'test': dict(name=u'testset')}, {})
        self.db.update_record(u'oai:spamspamspam',
                              datetime.datetime(2009, 06, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset')}, {})
        self.db.update_record(u'oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {u'ham': dict(name=u'hamset'),
                                      u'test': dict(name=u'testset')}, {})
        self.db.flush()
        # all records
        self.assertEquals([r['id'] for r in self.db.oai_query()],
                          [u'oai:ham', u'oai:spam', u'oai:spamspamspam'])
        # only set ham
        self.assertEquals([r['id'] for r in self.db.oai_query(
            needed_sets=[u'ham'])], [u'oai:ham'])
        # only set spam
        self.assertEquals([r['id'] for r in self.db.oai_query(
            needed_sets=[u'spam'])], [u'oai:spam', u'oai:spamspamspam'])
        # records in spam set and test set
        self.assertEquals([r['id'] for r in self.db.oai_query(
            needed_sets=[u'test', u'spam'])], [u'oai:spam'])
        # only allow records from certain sets
        self.assertEquals([r['id'] for r in self.db.oai_query(
            allowed_sets=[u'test'])], [u'oai:ham', u'oai:spam'])
        self.assertEquals([r['id'] for r in self.db.oai_query(
            allowed_sets=[u'spam', u'ham'])],
                          [u'oai:ham', u'oai:spam', u'oai:spamspamspam'])
        # only allow records from certain sets, combined with set
        self.assertEquals([r['id'] for r in self.db.oai_query(
            allowed_sets=[u'test'], needed_sets=['spam'])],
                          [u'oai:spam'])
        self.assertEquals([r['id'] for r in self.db.oai_query(
            allowed_sets=[u'spam'], needed_sets=['test'])],
                          [u'oai:spam'])
        # certain records should always be disallowed
        self.assertEquals([r['id'] for r in self.db.oai_query(
            disallowed_sets=[u'spam'])],
                           [u'oai:ham'])
        # disallowed sets has precedence over allowed sets
        self.assertEquals([r['id'] for r in self.db.oai_query(
            disallowed_sets=[u'test'], allowed_sets=[u'spam'])],
                           [u'oai:spamspamspam'])
    def test_oai_batching(self):
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset'),
                                      u'test': dict(name=u'testset')}, {})
        self.db.update_record(u'oai:spamspamspam',
                              datetime.datetime(2009, 06, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset')}, {})
        self.db.update_record(u'oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {u'ham': dict(name=u'hamset'),
                                      u'test': dict(name=u'testset')}, {})
        self.db.flush()
        self.assertEquals(len(list(self.db.oai_query())), 3)
        self.assertEquals(len(list(self.db.oai_query(batch_size=1))), 1)
        self.assertEquals([r['id'] for r in self.db.oai_query(
            batch_size=1)], [u'oai:ham'])
        self.assertEquals([r['id'] for r in self.db.oai_query(
            batch_size=1, offset=1)], [u'oai:spam'])
        self.assertEquals([r['id'] for r in self.db.oai_query(
            batch_size=1, offset=2)], [u'oai:spamspamspam'])

class ProviderTest(TestCase):
    def setUp(self):
        path = os.path.abspath(os.path.dirname(__file__))
        self.provider = FileBasedContentProvider(
            'file://%s/example*.xml' % path)
        self.db = Database()

    def tearDown(self):
        del self.provider
        del self.db

    def test_provider_update(self):
        self.assertEquals(sorted([id for id in self.provider.update()]),
                          ['example-1234.xml', 'example-2345.xml'])

    def test_provider_content(self):
        self.assertEquals(sorted([id for id in self.provider.update()]),
                          ['example-1234.xml', 'example-2345.xml'])
        for content_id in self.provider.get_content_ids():
            raw_data = self.provider.get_content_by_id(content_id)
            content = ExampleContent(self.provider)
            content.update(raw_data)
            self.db.update_record(content.id,
                                  content.modified,
                                  content.deleted,
                                  content.sets,
                                  content.metadata)
        self.db.flush()
        self.assertEquals(self.db.record_count(), 2)


class ServerTest(TestCase):
    def setUp(self):
        self.db = Database()
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset'),
                                      u'test': dict(name=u'testset')},
                              {'title': [u'Spam!']})
        self.db.update_record(u'oai:spamspamspam',
                              datetime.datetime(2009, 06, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset')},
                              {'title': [u'Spam Spam Spam!']})
        self.db.update_record(u'oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {u'ham': dict(name=u'hamset'),
                                      u'test': dict(name=u'testset')},
                              {'title': [u'Ham!']})
        self.db.flush()
        self.config = FeedConfig('Test Server',
                                 'http://test',
                                 admin_emails=['testuser@localhost'],
                                 metadata_prefixes=['oai_dc', 'mods', 'didl'])
        self.server = Server('http://test', self.db, self.config)
        self.app = MOAIWSGIApp(self.server)
        wsgi_intercept.add_wsgi_intercept('test', 80, lambda : self.app)
        
    def tearDown(self):
        
        wsgi_intercept.remove_wsgi_intercept('test', 80)
        del self.app
        del self.server
        del self.db
        del self.config
        
    def test_identify(self):
        xml = urllib2.urlopen('http://test?verb=Identify').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai" :"http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(xpath.string('//oai:repositoryName'),u'Test Server')
        
    def test_list_identifiers(self):
        xml = urllib2.urlopen('http://test?verb=ListIdentifiers'
                              '&metadataPrefix=oai_dc').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(xpath.strings('//oai:identifier'),
                          [u'oai:ham', u'oai:spam', u'oai:spamspamspam'])

    def test_list_with_dates(self):
        xml = urllib2.urlopen('http://test?verb=ListIdentifiers'
                              '&metadataPrefix=oai_dc&from=2010-01-01').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(xpath.strings('//oai:identifier'),
                          [u'oai:ham'])
        xml = urllib2.urlopen('http://test?verb=ListIdentifiers'
                              '&metadataPrefix=oai_dc&until=2010-01-01').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(xpath.strings('//oai:identifier'),
                          [u'oai:spam', u'oai:spamspamspam'])

    def test_list_records(self):
        xml = urllib2.urlopen('http://test?verb=ListRecords'
                              '&metadataPrefix=oai_dc').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/",
                       "dc": "http://purl.org/dc/elements/1.1/"})
        self.assertEquals(xpath.strings('//oai:identifier'),
                          [u'oai:ham', u'oai:spam', u'oai:spamspamspam'])
        self.assertEquals(xpath.strings('//dc:title'),
                          [u'Ham!', u'Spam!', u'Spam Spam Spam!'])
        xml = urllib2.urlopen('http://test?verb=ListRecords'
                              '&metadataPrefix=didl').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/",
                       "mods": "http://www.loc.gov/mods/v3"})
        self.assertEquals(xpath.strings('//mods:titleInfo/mods:title'),
                          [u'Ham!', u'Spam!', u'Spam Spam Spam!'])
        
    def test_list_sets(self):
        xml = urllib2.urlopen('http://test?verb=ListSets').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(sorted(xpath.strings('//oai:setName')),
                          [u'hamset', u'spamset', u'testset'])

    def test_list_hidden_sets(self):
        self.db.update_record(u'oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {u'spam': dict(name=u'spamset'),
                                      u'test': dict(name=u'testset',
                                                    hidden=True)},
                              {'title': [u'Spam!']})
        # note that we change the set through the record. It is important
        # that all the records have the same values for each set
        self.db.flush()
        xml = urllib2.urlopen('http://test?verb=ListSets').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        # a hidden set should not show up in a listSets request
        self.assertEquals(sorted(xpath.strings('//oai:setName')),
                          [u'hamset', u'spamset'])
        
        # however, we can use the hidden set to filter on
        self.config.sets_disallowed.append(u'test')
        xml = urllib2.urlopen('http://test?verb=ListIdentifiers'
                              '&metadataPrefix=oai_dc').read()
        doc = etree.fromstring(xml)
        xpath = XPath(doc, nsmap=
                      {"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEquals(xpath.strings('//oai:identifier'),
                          [u'oai:spamspamspam'])


def suite():    
    test_suite = TestSuite()
    test_suite.addTest(makeSuite(XPathUtilTest))
    test_suite.addTest(makeSuite(DatabaseTest))
    test_suite.addTest(makeSuite(ProviderTest))
    test_suite.addTest(makeSuite(ServerTest))
    # note that tests of the oai protocol itself are done in the
    # pyoai codebase
    return test_suite
