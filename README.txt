
Installing MOAI
===============

The MOAI Software can be run in any wsgi compliant server. 

MOAI comes with a development server that can be used for testing. In production mod_wsgi can be used to run Moai in the apache webserver.

Installation Steps
==================

MOAI is a normal python package. It is tested with python2.5 and 2.6. 
I recommend creating a virtualenv to install the package in.

http://pypi.python.org/pypi/virtualenv/

This makes development and deployment easier.
Instructions below are for unix, but MOAI should also work on Windows

Go into the MOAI directory with the setup.py, and run the virtualenv command

> cd moai
> virtualenv .

Now, activate the virtualenv

> source bin/activate

Install MOAI in the virtualenv using pip

> pip install -e .

(this will take a while)

When this process finishes, Moai and all its dependencies will be installed.

Running in development mode
===========================

The development server should never be used for production, it is convenient for testing and development. Note that you should always activate the virtualenv otherwise the dependecies will not be found

> cd moai
> source bin/activate
> ./bin/paster serve settings.ini

This will print something like:

  Starting server in PID 7306.
  Starting HTTP server on http://127.0.0.1:8080

You can now visit localhost:8080/oai to view the moai oaipmh feed. 

Configuring MOAI
================

Configuration is done in the settings.ini file. The default settings file uses the Paste#urlmap application to map wsgi applications to a url.

In the `composite:main` section there is a line:

/oai = moai_example

Which maps the /oai url to a Moai instance. 
This makes it easy to run many Maoi instances in one server, each with it's own configuration.

The app:moai_example configuration let's you specify the following options:

name
  The name of the oai feed (returned in Identify verb)
url
  The url of the oai feed (returned in oaipmh xml output)
admin_email
  The email adress of the amdin  (returned in Identify verb)
formats
  Available metadata formats
disallow_sets
  List of setspecs that are not allowed in the output of this feed
allow_sets
  If used, only sets listed here will be returned
database
  SQLAlchemy uri to identify the database for used for storage
provider
  Provider identifier where moai retrieves content from
content
  Class that maps metadata from provider format to moai format

Adding Content
==============

The Moai system is designed to periodically fetch content from a `provider`, and convert it to Moai's internal format, which can then be translated to the different metadata formats for the oaipmh feed.

Moai comes with an example that shows this principle:

In the moai/moai directory there are two XML files. Let's pretend these files are from a remote system, and we want to publish them with MOAI.

In the settings.ini file, the following option is specified:

`provider = file://moai/example-*.xml`

This tells moai that we want to use a file provider, with some files located in
`moai/example-*.xml`. 

The following option points to the class that we want to use for converting the example content xml data to Moais internal format.

content = moai_example

The last option tells Moai where to store it's data, this is usually a sqlite database:

database = sqlite:///moai-example.db

Now let's try to add these two xml files, let's first visit the oaipmh feed to make sure nothing is allready being served:

http://localhost:8080/oai?verb=ListRecords&metadataPrefix=oai_dc

This should return a noRecordsMatch error.

To add the content, run the update_content script, with the section name from the settings.ini as argument

> ./bin/update_moai moai_example

This will produce the following output:

/ Updating content provider: example-2345.xml                                   
Content provider returned 2 new/modified objects

100.0%[====================================================================>] 2
Updating database with 2 objects took 0 seconds

Now when you visit the oaipmh feed again you should see the two records:

http://localhost:8080/oai?verb=ListRecords&metadataPrefix=oai_dc

When you run the update_moai script again, it will create a new database with all the records (in this case moai_example.db). It is also possible to specify a data with the --date switch. When a data is specified, only records that were modified after this date will be added. 
The update_moai script can be run from a daily or hourly cron job to update the database

Adding your own Provider / Content and Metadata Classes
=======================================================

It's possible and most of the time, needed, to extend Moai for your use-cases.
The Provider and Content classes from the example might be a good starting point if you want to do that. All your customizations should be registered with Moai through `entry_points`. Have a look at Moais setup.py for more information.
The best approach would be to create your own python package with setup.py and install this in the same environment as Moai. This will let Moai find your customizations. Note that when you change something in your setup.py, you have to reinstall the package, for Moai to pick up the changes.

Note that the moai.interfaces file contains documentation about the different classes that you can implement.

Adding your own Database
========================

Instead of writing your own provider/content classes, you can also register your own custom database. Implementing a replacement for moai.database.SQLDatabase can be more complicated then writing a provider/content class, but it has the advantage that Moai is always up to date, and you don't need a second sqlite database.

Have a look at the setup.py file from the MOAI code, it registers several databases. You could use this mechanism to register your own database from your own python package.

In the settings.ini you configuration you can then reference your database ('mydb://some+config+variables').

For the database, have a look at the generic database provider in database.py. The only methods that you need to implement are: oai_sets, oai_earliest_datestamp and oai_query.
The oai_query method returns dictionaries with record data. The keys of these dictionaries are defined in the metadata files (for example metadata.py),  have a look at the source. 

For oai_dc there are the following names:

'title', 'creator', 'subject', 'description', 'publisher', 'contributor', 'type', 'format', 'identifier', 'source', 'language', 'date', 'relation', 'coverage', 'rights

So a return value would look like::

    {'id': <oai record id>,
     'deleted': <bool>,
     'modified': <utc datetime>,
     'sets': <list of setspecs>,
     'metadata': {
       'title': [<list with publication title>],
       'creator': [<list of creator names>],
       ...}
    }

 




