MOAI
====

The Meta OAI Server.

We start by importing the MOAI package
>>> import moai

Moai uses logging extensively, let's make a log instance first
>>> import logging
>>> log = logging.getLogger('moai')

We now create the core MOAI object, this will register some 
pluggable extensions.

>>> from moai.core import MOAI
>>> moai = MOAI(log)

Lets make some fake data:

>>> content = [{'id':u'tester',
...            'label':u'Tester',
...            'content_type': u'document',
...            'when_modified': datetime.datetime(2008, 10, 29, 13, 25, 00),
...            'deleted':False,
...            'sets':[u'stuff'],
...            'is_set': False,
...            'title':[u'This is a test']},
...            {'id':u'stuff', 
...            'label':u'Stuff',
...            'content_type': u'collection',
...            'when_modified': datetime.datetime.now(),
...            'deleted':False,
...            'sets':[],
...            'is_set': True
...            }]

Now we will use a simple list based content provider
to consume that data. There can be many types of content
providers, such as file based content providers, or content
providers that get their data out of a database

>>> from moai.provider.list import ListBasedContentProvider
>>> p = ListBasedContentProvider(content)


A content provider is a list of records. Before you can use it,
it needs to be updated. The update call, returns a list of 
record_ids that where updated. Optionally you can supply a date

>>> sorted(p.update())
[0, 1]

We can now ask how many records it holds

>>> p.count()
2

We can get the object back by id. But what the id is, depends
on the provider. A provider does not known what kind of content
it is serving. So we can not use the 'id' key from the content.
A ListBasedContentProvider used the index number as id

>>> d = p.get_content_by_id(0)
>>> d['id']
u'tester'

We can also get all the content ids from the provider, 
and use that to get the content.

>>> sorted(p.get_content_ids())
[0, 1]

Now we can create a content object from the data, normally
this will be done by the databaseUpdater class

>>> from moai.content import DictBasedContentObject
>>> c = DictBasedContentObject()
>>> c.update(d, p)

Besides some of the required values a content object must have,
it can also have an arbitrary number of other values. We can ask
the content object what theyre names are:

>>> c.field_names()
['title']

We can then get the values. Note that this should always return a list
>>> c.get_values('title')
[u'This is a test']

We can periodicly ask the dataprovider to update its list of content objects
A date is supplied so the provider only has to look for new objects younger
then that date. The update call will return a list of new found ids

>>> p.update(datetime.datetime.now())
[1]

Now we create a new fresh database. We can use all sorts of databases, as long
as it implements the IDatabase interface. The btree database stores everything in
a file, or in memory if no arguments are passed.

>>> from moai.database.btree import BTreeDatabase
>>> db = BTreeDatabase()

To get the content into the database we use a DatabaseUpdater

>>> from moai.update import DatabaseUpdater

We pass the database and the contentProvider to the updater, a contentObject class
is also needed, to convert the data provided into an interface, the updater 
understands. a log instance is also needed.

>>> updater = DatabaseUpdater(p, DictBasedContentObject, db, log)

Now we will update the database, but before we do that, we need to update
the provider.. 

>>> updater.update_provider()
[0, 1]
>>> updater.update_database()
0

Note that this function calls update_database_iterate, which 
gives more feedback, and can be used to track the progress of
the update.

Lets see if we can retrieve some data from the database

>>> sorted(db.get_record('tester').keys())
['content_type', 'deleted', 'id', 'is_set', 'sets', 'when_modified']

>>> db.get_metadata('tester')
{'title': [u'This is a test']}

The database also provides some extra methods used by the oai
Server. One of these is list_sets:

>>> list(db.oai_sets())[0]['name']
u'Stuff'

All the other OAI requests will call a single method on the 
database called oai_query

>>> len(list(db.oai_query()))
1

OAI Server
----------

Now that we have our OAI database setup, we can serve it to 
the world. The OAI Server can serve multiple OAI feeds, 
each with it's own configuration. 

>>> from moai.server import Server, FeedConfig
>>> from moai.http.cgi import CGIRequest
>>> config = FeedConfig('test',
...                       'A test repository',
...                       'http://localhost/repo/test',
...                        log) 
>>> s = Server('http://localhost/repo', db)
>>> s.add_config(config)
>>> req = CGIRequest('http://localhost/repo/test', verb='Identify')
>>> s.handle_request(req)
Status: 200 OK
...
<Identify>
<repositoryName>A test repository</repositoryName>
...
</Identify>
...

Cool! Lets see what happens if we use a different url

>>> req = CGIRequest('http://localhost/repo/bla', verb='Identify')
>>> s.handle_request(req)
Status: 404 ...
...

Right, that makes sense. Now let's see what happens if we add a wrong verb

>>> req = CGIRequest('http://localhost/repo/test', verb='Bla')
>>> s.handle_request(req)
Status: 200 ...
Content-Type: text/xml
...
<error code="badVerb">Illegal verb: Bla</error>
...

That seems to work.. We're not going to test the full server here. That's been done
in the pyoai tests.

Now let's see if we can get a list of sets the server supports

>>> req = CGIRequest('http://localhost/repo/test', verb='ListSets')
>>> s.handle_request(req)
Status: 200 ...
...
<set>
<setSpec>set_stuff</setSpec>
<setName>Stuff</setName>
</set>
...

We will now get the ids of the Records

>>> req = CGIRequest('http://localhost/repo/test',
...                  verb='ListIdentifiers',
...                  metadataPrefix='oai_dc')
>>> s.handle_request(req)
Status: 200 ...
...
<ListIdentifiers>
<header>
<identifier>oai:tester</identifier>
<datestamp>2008-10-29T13:25:00Z</datestamp>
<setSpec>set_stuff</setSpec>
</header>
</ListIdentifiers>
...

Now, let's get the full records:
>>> req = CGIRequest('http://localhost/repo/test',
...                  verb='ListRecords',
...                  metadataPrefix='oai_dc')
>>> s.handle_request(req)
Status: 200 ...
...
<dc:title>This is a test</dc:title>
...

Assets
------

MOAI can also serve asset files, we can ask the MOAI database 
if a record has assets

>>> db.get_assets(u'tester')
[]

Let's add an asset with some assets
>>> content[0]['assets'] = [{'filename': u'test.txt',
...                          'mimetype': u'text/plain',
...                          'url': u'http://www.example.com',
...                          'absolute_uri': u'file:///test.txt',
...                          'md5': u'1234',
...                          'metadata': {u'foo': [u'bar']}}]

Let's update the provider, and get the content object

>>> p = ListBasedContentProvider(content)
>>> c = DictBasedContentObject()
>>> c.update(d, p.get_content_by_id(0))

A content object has a method to retrieve a list of assets
dictionaries

>>> c.get_assets()
[{...test.txt...}]

Let's update the database with the new content

>>> db = BTreeDatabase()
>>> updater = DatabaseUpdater(p, DictBasedContentObject, db, log)
>>> updater.update_provider()
[0, 1]
>>> updater.update_database()
0

The database has a similar method to retrieve the assets from a record
>>> assets = db.get_assets(u'tester')
>>> len(assets)
1
>>> asset = assets[0]

An asset dictionary always has the following keys
>>> sorted(asset.keys())
['absolute_uri', 'filename', 'md5', 'metadata', 'mimetype', 'url']

Additional values can be stored in the metadata dict

>>> asset['metadata']
{u'foo': [u'bar']}

The assets can be served by the OAI server as part of an oai feed
By default the path will be <basepath>/<id>/<filename> where
basepath defaults to the systems temp dir. 
The basepath and the resolving to the asset file can be configured
in the FeedConfig objects.

Let's put a textfile in the right directory, and see if we
can open it through the server

>>> import os, tempfile
>>> path = tempfile.gettempdir() + '/tester'
>>> if not os.path.isdir(path): 
...    os.mkdir(path)
>>> open(path + '/test.txt', 'w').write('Hello Asset World')

Now, let's do a webrequest for the asset.

>>> s = Server('http://localhost/repo', db)
>>> s.add_config(config)
>>> req = CGIRequest('http://localhost/repo/test/asset/tester/test.txt')
>>> s.handle_request(req)
Status: 200 OK
Content-Type: text/plain
Content-Length: 17
<BLANKLINE>
Hello Asset World

Cool, that seems to work.

If we try to get a non existing file, the server returns
a http 404 status

>>> req = CGIRequest('http://localhost/repo/test/asset/tester/foo.txt')
>>> s.handle_request(req)
Status: 404 File not Found
Content-Type: text/plain
Content-Length: 34
<BLANKLINE>
The asset "foo.txt" does not exist

Now let's clean up the asset directory

>>> if os.path.isdir(path):
...    import shutil
...    shutil.rmtree(path)
