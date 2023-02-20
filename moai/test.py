# coding=utf8
import datetime
import doctest
import os
from unittest import makeSuite, TestCase, TestSuite

import requests
from lxml import etree
from wsgi_intercept import add_wsgi_intercept, requests_intercept

from moai.database import SQLDatabase
from moai.example import ExampleContent
from moai.provider.file import FileBasedContentProvider
from moai.server import FeedConfig, Server
from moai.utils import XPath
from moai.wsgi import MOAIWSGIApp

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
        self.assertEqual(xpath.strings('/doc/string'),
                         ['test', 'test', 'test', 'tëst'])

    def test_boolean(self):
        doc = etree.fromstring(
            '''<doc>
                 <bool>yes</bool>
                 <bool>true</bool>
                 <bool>False</bool>
                 <bool>NO</bool>
               </doc>''')
        xpath = XPath(doc)
        self.assertEqual(xpath.booleans('/doc/bool'),
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
        self.assertEqual(numbers,
                         [1, 3.33333333333, -75, -0.75])
        self.assertEqual([type(i) for i in numbers],
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
        self.assertEqual(xpath.dates('/doc/date'),
                         [datetime.datetime(2010, 1, 4, 0, 0),
                          datetime.datetime(2010, 1, 4, 0, 0),
                          datetime.datetime(2010, 1, 4, 12, 43, 33),
                          datetime.datetime(2010, 1, 4, 12, 43, 33)])

    def test_tags(self):
        doc = etree.fromstring('<doc><a/><b/><s:c xmlns:s="urn:spam"/></doc>')
        xpath = XPath(doc)
        self.assertEqual(xpath.tags('/doc/*'), ['a', 'b', 'c'])

    def test_namespaces(self):
        doc = etree.fromstring(
            '<doc xmlns="urn:spam"><string>Spam!</string></doc>')
        xpath = XPath(doc, nsmap={'spam': 'urn:spam'})
        self.assertEqual(xpath.string('//spam:string'), 'Spam!')


class DatabaseTest(TestCase):
    def setUp(self):
        self.db = SQLDatabase()

    def tearDown(self):
        del self.db

    def test_update(self):
        # db is empty
        self.assertEqual(self.db.record_count(), 0)
        # let's add a record
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {},
                              {'title': 'Spam!'})
        self.db.flush()
        self.assertEqual(self.db.record_count(), 1)
        # check if all values are there
        record = self.db.get_record('oai:spam')
        self.assertEqual(record['id'], 'oai:spam')
        self.assertEqual(record['deleted'], False)
        self.assertEqual(record['modified'],
                         datetime.datetime(2010, 10, 13, 12, 30, 00))
        self.assertEqual(record['sets'], [])
        self.assertEqual(record['metadata'], {'title': 'Spam!'})
        # change a metadata value
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 0o1),
                              False,
                              {},
                              {'title': 'Ham!'})
        self.db.flush()
        self.assertEqual(self.db.record_count(), 1)
        # check if metadata was changed
        record = self.db.get_record('oai:spam')
        self.assertEqual(record['metadata'], {'title': 'Ham!'})
        # remove the record
        self.db.remove_record('oai:spam')
        self.assertEqual(self.db.record_count(), 0)

    def test_setrefs(self):
        # add a record that references a set
        self.assertEqual(self.db.set_count(), 0)
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {'spamset': {'name': 'Spam Set',
                                           'description': 'spam spam spam',
                                           'hidden': False}},
                              {'title': 'Spam!'})
        self.db.flush()
        self.assertEqual(self.db.record_count(), 1)
        self.assertEqual(self.db.set_count(), 1)
        # check if all values are there
        record = self.db.get_record('oai:spam')
        self.assertEqual(record['sets'], ['spamset'])
        set = self.db.get_set('spamset')
        self.assertEqual(set['id'], 'spamset')
        self.assertEqual(set['name'], 'Spam Set')
        self.assertEqual(set['description'], 'spam spam spam')
        self.assertEqual(set['hidden'], False)
        # now, we'll change the record to use the hamset
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {'hamset': {'name': 'Ham Set',
                                          'description': 'ham ham ham',
                                          'hidden': False}},
                              {'title': 'Ham!'})
        self.db.flush()
        self.assertEqual(self.db.record_count(), 1)
        # note that we now have 2 sets, the spam set is not removed
        self.assertEqual(self.db.set_count(), 2)
        # however, the spam record only has one reference
        record = self.db.get_record('oai:spam')
        self.assertEqual(record['sets'], ['hamset'])
        # if the set is removed then all references to that set are
        # also removed
        self.db.remove_set('hamset')
        record = self.db.get_record('oai:spam')
        self.assertEqual(record['sets'], [])
        self.assertEqual(self.db.set_count(), 1)

    def test_hidden_sets(self):
        # hidden sets are not added to the record setrefs list,
        # they are there though, for filtering purposes
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False,
                              {'spamset': {'name': 'Spam Set',
                                           'description': 'spam spam spam',
                                           'hidden': False},
                               'hamset': {'name': 'Ham Set',
                                          'description': 'ham ham ham',
                                          'hidden': True}},
                              {'title': 'Spam!'})
        self.db.flush()
        self.assertEqual(self.db.get_setrefs('oai:spam'), ['spamset'])
        self.assertEqual(self.db.get_setrefs('oai:spam',
                                             include_hidden_sets=True),
                         ['hamset', 'spamset'])
        # hidden sets are also never shown in the oai sets listing
        self.assertEqual(list(self.db.oai_sets()),
                         [{'description': 'spam spam spam',
                           'id': 'spamset',
                           'name': 'Spam Set'}])

    def test_earliest_datestamp(self):
        self.assertEqual(self.db.oai_earliest_datestamp(),
                         datetime.datetime(1970, 1, 1, 0, 0))
        self.db.update_record('oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {}, {})
        self.db.update_record('oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {}, {})
        self.db.flush()
        self.assertEqual(self.db.oai_earliest_datestamp(),
                         datetime.datetime(2009, 10, 13, 12, 30))

    def test_oai_query_dates(self):
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 0o1, 0o1, 00, 00, 00),
                              False, {'spamset': {'name': 'spam'}},
                              {})
        self.db.update_record('oai:ham',
                              datetime.datetime(2009, 0o1, 0o1, 00, 00, 00),
                              False, {'hamset': {'name': 'ham'}},
                              {})
        self.db.flush()
        self.assertEqual(
            list(self.db.oai_query()),
            [{'deleted': False,
              'sets': ['spamset'],
              'metadata': {},
              'id': 'oai:spam',
              'modified': datetime.datetime(2010, 1, 1, 0, 0)},
             {'deleted': False,
              'sets': ['hamset'],
              'metadata': {},
              'id': 'oai:ham',
              'modified': datetime.datetime(2009, 1, 1, 0, 0)}])
        # date slices
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                from_date=datetime.datetime(2009, 6, 1, 0, 0))],
            ['oai:spam'])
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                until_date=datetime.datetime(2009, 6, 1, 0, 0))],
            ['oai:ham'])
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                from_date=datetime.datetime(2008, 6, 1, 0, 0),
                until_date=datetime.datetime(2010, 6, 1, 0, 0))],
            ['oai:spam', 'oai:ham'])
        # no matches
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                from_date=datetime.datetime(2011, 1, 1, 0, 0))],
            [])
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                until_date=datetime.datetime(2008, 1, 1, 0, 0))],
            [])
        # test inclusiveness
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(
                from_date=datetime.datetime(2009, 1, 1, 0, 0),
            )],
            ['oai:spam', 'oai:ham'])

    def test_oai_query_identifier(self):
        self.db.update_record('oai:spam',
                              datetime.datetime(2010, 0o1, 0o1, 00, 00, 00),
                              False, {'spamset': {'name': 'spam'}},
                              {})
        self.db.flush()
        self.assertEqual(
            [r['id'] for r in self.db.oai_query(identifier='oai:spam')],
            ['oai:spam'])

    def test_oai_query_future_dates(self):
        # records with a timestamp in the future should never
        # be returned, this feature can be used to create embargo dates
        self.db.update_record('oai:spam',
                              datetime.datetime(2040, 0o1, 0o1, 00, 00, 00),
                              False, {'spamset': {'name': 'spam'}},
                              {})
        self.db.flush()
        self.assertEqual(list(self.db.oai_query()), [])
        self.assertEqual(list(self.db.oai_query(
            until_date=datetime.datetime(2050, 0o1, 0o1, 00, 00, 00))), [])
        self.assertEqual(list(self.db.oai_query(identifier='oai:spam')), [])

    def test_oai_sets(self):
        self.db.update_record('oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset'),
                                      'test': dict(name='testset')}, {})
        self.db.update_record('oai:spamspamspam',
                              datetime.datetime(2009, 0o6, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset')}, {})
        self.db.update_record('oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {'ham': dict(name='hamset'),
                                      'test': dict(name='testset')}, {})
        self.db.flush()
        # all records
        self.assertEqual([r['id'] for r in self.db.oai_query()],
                         ['oai:ham', 'oai:spam', 'oai:spamspamspam'])
        # only set ham
        self.assertEqual([r['id'] for r in self.db.oai_query(
            needed_sets=['ham'])], ['oai:ham'])
        # only set spam
        self.assertEqual([r['id'] for r in self.db.oai_query(
            needed_sets=['spam'])], ['oai:spam', 'oai:spamspamspam'])
        # records in spam set and test set
        self.assertEqual([r['id'] for r in self.db.oai_query(
            needed_sets=['test', 'spam'])], ['oai:spam'])
        # only allow records from certain sets
        self.assertEqual([r['id'] for r in self.db.oai_query(
            allowed_sets=['test'])], ['oai:ham', 'oai:spam'])
        self.assertEqual([r['id'] for r in self.db.oai_query(
            allowed_sets=['spam', 'ham'])],
            ['oai:ham', 'oai:spam', 'oai:spamspamspam'])
        # only allow records from certain sets, combined with set
        self.assertEqual([r['id'] for r in self.db.oai_query(
            allowed_sets=['test'], needed_sets=['spam'])],
            ['oai:spam'])
        self.assertEqual([r['id'] for r in self.db.oai_query(
            allowed_sets=['spam'], needed_sets=['test'])],
            ['oai:spam'])
        # certain records should always be disallowed
        self.assertEqual([r['id'] for r in self.db.oai_query(
            disallowed_sets=['spam'])],
            ['oai:ham'])
        # disallowed sets has precedence over allowed sets
        self.assertEqual([r['id'] for r in self.db.oai_query(
            disallowed_sets=['test'], allowed_sets=['spam'])],
            ['oai:spamspamspam'])

    def test_oai_batching(self):
        self.db.update_record('oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset'),
                                      'test': dict(name='testset')}, {})
        self.db.update_record('oai:spamspamspam',
                              datetime.datetime(2009, 0o6, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset')}, {})
        self.db.update_record('oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {'ham': dict(name='hamset'),
                                      'test': dict(name='testset')}, {})
        self.db.flush()
        self.assertEqual(len(list(self.db.oai_query())), 3)
        self.assertEqual(len(list(self.db.oai_query(batch_size=1))), 1)
        self.assertEqual([r['id'] for r in self.db.oai_query(
            batch_size=1)], ['oai:ham'])
        self.assertEqual([r['id'] for r in self.db.oai_query(
            batch_size=1, offset=1)], ['oai:spam'])
        self.assertEqual([r['id'] for r in self.db.oai_query(
            batch_size=1, offset=2)], ['oai:spamspamspam'])


class ProviderTest(TestCase):
    def setUp(self):
        path = os.path.abspath(os.path.dirname(__file__))
        self.provider = FileBasedContentProvider(
            'file://%s/testdata/example*.xml' % path)
        self.db = SQLDatabase()

    def tearDown(self):
        del self.provider
        del self.db

    def test_provider_update(self):
        self.assertEqual(sorted([id for id in self.provider.update()]),
                         ['example-1234.xml', 'example-2345.xml'])

    def test_provider_content(self):
        self.assertEqual(sorted([id for id in self.provider.update()]),
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
        self.assertEqual(self.db.record_count(), 2)


class ServerTest(TestCase):
    def setUp(self):
        self.db = SQLDatabase()
        self.db.update_record('oai:spam',
                              datetime.datetime(2009, 10, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset'),
                                      'test': dict(name='testset')},
                              {'title': ['Spam!']})
        self.db.update_record('oai:spamspamspam',
                              datetime.datetime(2009, 0o6, 13, 12, 30, 00),
                              False, {'spam': dict(name='spamset')},
                              {'title': ['Spam Spam Spam!']})
        self.db.update_record('oai:ham',
                              datetime.datetime(2010, 10, 13, 12, 30, 00),
                              False, {'ham': dict(name='hamset'),
                                      'test': dict(name='testset')},
                              {'title': ['Ham!']})
        self.db.flush()
        self.config = FeedConfig('Test Server',
                                 'http://test',
                                 admin_emails=['testuser@localhost'],
                                 metadata_prefixes=['oai_dc', 'mods', 'didl'])
        self.server = Server('http://test', self.db, self.config)
        self.app = MOAIWSGIApp(self.server)
        requests_intercept.install()
        add_wsgi_intercept('test', 80, lambda: self.app)

    def tearDown(self):

        requests_intercept.uninstall()
        del self.app
        del self.server
        del self.db
        del self.config

    def test_identify(self):
        response = requests.get('http://test?verb=Identify')
        doc = etree.fromstring(response.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEqual(xpath.string('//oai:repositoryName'), 'Test Server')

    def test_list_identifiers(self):
        response = requests.get('http://test?verb=ListIdentifiers&metadataPrefix=oai_dc')
        doc = etree.fromstring(response.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEqual(xpath.strings('//oai:identifier'),
                         ['oai:ham', 'oai:spam', 'oai:spamspamspam'])

    def test_list_with_dates(self):
        response_from = requests.get('http://test?verb=ListIdentifiers&metadataPrefix=oai_dc&from=2010-01-01')
        doc = etree.fromstring(response_from.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEqual(xpath.strings('//oai:identifier'),
                         ['oai:ham'])
        response_until = requests.get('http://test?verb=ListIdentifiers&metadataPrefix=oai_dc&until=2010-01-01')
        doc = etree.fromstring(response_until.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/"})
        self.assertEqual(xpath.strings('//oai:identifier'),
                         ['oai:spam', 'oai:spamspamspam'])

    def test_list_records(self):
        response1 = requests.get('http://test?verb=ListRecords&metadataPrefix=oai_dc')
        doc = etree.fromstring(response1.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/",
                                  "dc": "http://purl.org/dc/elements/1.1/"})
        self.assertEqual(xpath.strings('//oai:identifier'),
                         ['oai:ham', 'oai:spam', 'oai:spamspamspam'])
        self.assertEqual(xpath.strings('//dc:title'),
                         ['Ham!', 'Spam!', 'Spam Spam Spam!'])

        response2 = requests.get('http://test?verb=ListRecords&metadataPrefix=didl')
        doc = etree.fromstring(response2.content)
        xpath = XPath(doc, nsmap={"oai": "http://www.openarchives.org/OAI/2.0/",
                                  "mods": "http://www.loc.gov/mods/v3"})
        self.assertEqual(xpath.strings('//mods:titleInfo/mods:title'),
                         ['Ham!', 'Spam!', 'Spam Spam Spam!'])

    def test_list_sets(self):
        response = requests.get('http://test?verb=ListSets')
        doc = etree.fromstring(response.content)
        # Sets have been disabled in the UU version of MOAI
        self.assertTrue('<error code="noSetHierarchy"></error>' in str(response.content))

def suite():
    test_suite = TestSuite()
    test_suite.addTest(makeSuite(XPathUtilTest))
    test_suite.addTest(makeSuite(DatabaseTest))
    test_suite.addTest(makeSuite(ProviderTest))
    test_suite.addTest(makeSuite(ServerTest))
    # note that tests of the oai protocol itself are done in the
    # pyoai codebase
    return test_suite
