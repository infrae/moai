
MOAI, an Open Access Server Platform for Institutional Repositories
===================================================================

MOAI is a platform for aggregating content from different sources, and publishing it through the Open Archive Initiatives protocol for metadata harvesting.
It's been built for academic institutional repositories dealing with relational metadata and asset files.

What does it do?
----------------

The MOAI software can aggregate content from different sources, transform it and store it in a database. The contents of this database can then be published in many separate OAI feeds, each with its own configuration. 

The MOAI software has a very flexible system for combining records into sets, and can use these sets in the feed configuration. It also comes with a simple yet flexible authentication scheme that can be easily customized. Besides providing authentication for the feeds, the authentication also controls the access to the assets. 

Why MOAI
--------

MOAI has been specifically developed for universities, and contains a lot of hard-earned wisdom. The software has been in production use since 2007, and new features have been continually added. In late 2008, the software was completely refactored and packaged under the name "MOAI". You can read more about this on the `MOAI History`_ page.

MOAI is a standalone system, so it can be used in combination with any repository software that comes with an OAI feed such as `Fedora Commons`_, `EPrints`_ or `DSpace`_. It can also be used directly with an SQL database or just a folder of XML files.

The MOAI project takes the philosophy that every repository is different and unique, and that an institutional repository is a living thing. It is therefore never finished. Metadata is always changes, improving, and evolves. We think this is healthy. 

Because of this viewpoint, the MOAI software makes it as easy as possible to add or modify parts of your repository (OAI) services stack. It tries to do this without sacrificing power, and encouraging the re-use of components.

Features
--------

MOAI has some interesting features not found in most OAI servers. 
Besides serving OAI, it can also harvest OAI. This makes it possible for MOAI to work as a pipe, where the OAI data can be reconfigured, cached, and enriched while it passes through the MOAI processing.

More specifically MOAI has the ability to:

- Harvest data from different kinds of sources
- Serve many OAI feeds from one MOAI server, each with their own configuration
- Turn metadata values into OAI sets on the fly, creating new collections
- Use OAI sets to filter records shown in a feed, configurable for each feed
- Work easily with relational data (e.g. if an author changes, the publication should also change)
- Simple and robust authentication through integration with the Apache webserver
- Serve assets via Apache while still using configurable authentication rules

In the coming period we will be adding more features and updating this page accordingly. 

.. _MOAI History: http://moai.infrae.com/history.html
.. _Fedora Commons: http://www.fedora.info
.. _EPrints: http://www.eprints.org
.. _DSpace: http://www.dspace.org/
