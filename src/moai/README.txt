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

We also need to pass in a content class, that knows how to dealt with
the data returned by the provider. In this case, it's a dictionary, so
we'll use a content class that can handle dictionaries

>>> from moai.content import DictBasedContentObject
>>> p.set_content_class(DictBasedContentObject)


A content provider is a list of records. We can ask how
many records it holds

>>> p.count()
2

We can also get all the content objects from the provider, 

>>> c = list(p.get_content())[0]
>>> c.id
u'tester'

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
[]

Now we create a new fresh database. We can use all sorts of databases, as long
as it implements the IDatabase interface. The btree database stores everything in
a file, or in memory if no arguments are passed.

>>> from moai.database import BTreeDatabase
>>> db = BTreeDatabase()

To get the content into the database we use a DatabaseUpdater

>>> from moai.update import DatabaseUpdater

We pass the database and the content to the updater, a log instance is also
needed

>>> updater = DatabaseUpdater(p, db, log)

Now we update the database.. 

>>> updater.update()
<generator object ...>

Note that this method returns a generator with progress information
we have to iterate through the results to make sure everything is updated

>>> for c in updater.update():pass

Lets see if we can retrieve some data from the database

>>> sorted(db.get_record('tester').keys())
['content_type', 'deleted', 'id', 'when_modified']

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

Now that we have our OAI database setup, we can serve it to 
the world. The OAI Server can serve multiple OAI feeds, 
each with it's own configuration. 

>>> from moai.server import Server, ServerConfig, CGIRequest
>>> config = ServerConfig('test',
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
<setSpec>stuff</setSpec>
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

