MOAI
====

The Meta OAI Server.

We start by importing the MOAI package
>>> import moai

Lets make some fake data:

>>> content = [{'id':u'tester',
...            'content_type': u'document',
...            'when_modified': datetime.datetime(2008, 10, 29, 13, 25, 00),
...            'deleted':False,
...            'scope':u'public',
...            'sets':[u'stuff'],
...            'title':[u'This is a test']}]
>>> sets = [{'id':u'stuff', 
...          'name':u'Stuff',
...          'description':u'a set with some stuff'}]

Now we will use a simple list based content provider
to consume that data. There can be many types of content
providers, such as file based content providers, or content
providers that get their data out of a database

>>> from moai.content import ListBasedContentProvider
>>> p = ListBasedContentProvider(content, sets)

A content provider is a list of records. We can ask how
many records it holds

>>> p.count()
1

The data should have certain values, to make the provider work,
a content object should always have a unique ID. We can use this id
to retrieve a single content object

>>> c = p.get_content_by_id('tester')

We can also get all content objects in a generator, 

>>> list(p.get_content())[0].id == c.id
True

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
then that date.

>>> p.update(datetime.datetime.now())
[]

Now we create a new fresh database. We can use all sorts of databases, as long
as it implements the IDatabase interface. The btree database stores everything in
a file, or in memory if no arguments are passed.

>>> from moai.database import BTreeDatabase
>>> db = BTreeDatabase()

To get the content into the database we use a DatabaseUpdater

>>> from moai.content import DatabaseUpdater

We pass the database and the content to the updater, a log instance is also
needed

>>> import logging
>>> updater = DatabaseUpdater(p, db, logging)

Now we update the database..

>>> updater.update()
True

Lets see if we can retrieve some data from the database

>>> sorted(db.get_record('tester').keys())
['content_type', 'deleted', 'id', 'scope', 'when_modified']

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
...                        logging) 
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

