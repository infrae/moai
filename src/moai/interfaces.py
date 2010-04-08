from zope.interface import Interface, Attribute

class IContentProvider(Interface):
    """Object that provides the content used to build the database
    that is used to serve the actual oai data
    """

    def set_logger(self, log):
        """Set the logger instance for this class
        """

    def update(from_date=None):
        """Harvests new content added since from_date
        returns a list of content_ids that were changed/added,
        this should be called before get_contents is called
        """
        pass

    def count():
        """Returns number of content objects in the repository
        returns None if number is unknown, this should not be
        called before update is called
        """

    def get_content_ids():
        """returns a list/generator of content_ids
        """

    def get_content_by_id():
        """Return content of a specific id
        """

class IContentObject(Interface):

    id = Attribute(u"Id of the content object")
    label = Attribute(u"Name of the object")
    content_type = Attribute(u"Type of the content object")
    when_modified = Attribute(u"Modification date of the object")
    deleted = Attribute(u"Boolean that tells if object is deleted or not")
    sets = Attribute(u"A list of ids from sets that this object belongs to")
    is_set = Attribute(u"Boolean indicating if this object is a set")

    provider = Attribute(u"ContentProvider instance that created this object")

    def update(data, provider):
        """Called by IContentProvider, to fill the object with data
        """
        
    def field_names():
        """Return a list of field names, used in this object
        """

    def get_values(field_name):
        """Return a list of python objects (string/int/etc)
        from a specific field name
        """

    def get_assets():
        """Return a list of python dictionaries, each dictionary contains
        at least the following keys:

        - url               - Url of the asset, this will be used in feeds
        - filename          - The filename of the asset
        - md5sum            - md5 checksum of the asset
        - mimetype          - mimetype of the asset
        - absolute_uri      - file:/// or http:/// uri referencing the file
        - metadata          - dictionary with lists of strings as values holding
                              additional metadata
        """
        

        
class IContentValidator(Interface):

    content_type = Attribute("The type of objects this validator can validate")

    def set_logger(logger_instance):
       """Make the validator use a specific custom logger
       (will probably be set automaticly in __init__)
       """
   
    def validate_object(content_object):
        """Validates an object, return a Boolean to indicate validity,
        Alle warnings and errors, should also be logged with the log object
        that's provided as an argument of the set_logger method
        """
    
class IDatabaseUpdater(Interface):

    flush_limit = Attribute('''
        Flush database after processing n records. 
        Defaults to -1, which only flushes the database
        at the end''')

    def set_database(database):
        """Make the updater use a specific (new) database
        (will probably be set automaticly in __init__)
        """

    def set_content_provider(content_provider):
        """Make the updater use a specific ContentProvider
        (will probably be set automaticly in __init__)
        """

    def set_content_class(self, content_object_class):
        """Sets the class to be used to create the content objects
        from the provider data
        """
    
    def set_logger(logger_instance):
       """Make the updater use a specific custom logger
       (will probably be set automaticly in __init__)
       """

    def update_provider(from_date=None):
        """Iterates through update_provider_iterate in a loop,
        returns a list of updated ids
        """

    def update_provider_iterate(from_date=None):
       """Updates the provider from a specific date,
       yields the ids that where updated
       """
   
    def update_database(validate=True, supress_errors=False):
        """Iterates through update_database_iterate in a loop,
        returns the number of errors that occured (int)
        """
    
    def update_database_iterate(validate=True, supress_errors=False):
        """Update the database with the content_provider
        this will update the content_provider, optionally
        validate the content objects, and add everything
        to the database.
        If supress_errors is True, this method should
        never return an error, instead it should
        yield tuples containing the following values:

        (count, total, provider_id, exception)

        count: current content object number
        total: total number of objects
        provider_id: id used by provider
        exception: if an error occurs, exception should be a
                   moai.ContentError, or a moai.DatabaseError
                   otherwise this value will be None

        After the database update is finished, the flush_update method
        of the database is called. This allows the database to
        implement a batching strategy
        """

class IReadOnlyDatabase(Interface):

    def oai_sets(offset=0, batch_size=20):
        """Used by queries from the OAI server. Format returned should be the
        following:

        [{'id': <string>,
          'name': <string>,
          'description': <string>}]
          
        """
    
    def oai_query(offset=0,
                  batch_size=20,
                  sets=[],
                  not_sets=[],
                  filter_sets=[],
                  from_date=None,
                  until_date=None,
                  identifier=None):
        """Used by queries from the OAI server. Format returned should be the
        following:

        [{'record': <dict similar to get_record() output>,
          'metadata': <dict similar to get_metadata() output>,
          'assets': <dict similar to get_assets() output>}
        ]
        """

        
    def get_record(id):
        """Returns a dictionary of data that is available from the
        object with the specific id. The dictionary should contain at least
        the following data:

        {'id': unicode,
        'when_modified': dateTime,
        'deleted': boolean,
        'sets': list of strings,
        }

        If the id does not exist, None is returned
        """

    def get_metadata(id):
        """Returns a dictionary with additional data.
        Keys are always a string, values are always lists of python
        objects.
        
        If the id does not exist, None is returned
        """

    def get_sets(id):
        """Returns a list of set ids for a specific id,
        """

    def get_set(id):
        """Returns a dictionary of set info containing
        - id
        - name
        - description
        
        If the id does not exist, None is returned
        """

    def get_assets(id):
        """Returns a list of dictionaries describing the assets
        Each dictionary contains the following fields:
        - filename
        - url
        - mimetype
        - md5
        - absolute_uri
        - metadata
        
        Where metadata is a dictionary with additional lists of string values
        """

class IDatabase(IReadOnlyDatabase):

    def flush_update():
        """Called once by the database updater at the end of the update proces
        (depending on the flush_threshold attribute in DatabaseUpdater)
        This allows the database to implement a batching strategy
        """
        
    def remove_content(id):
        """Remove all the content of a given id, returns a boolean to indicate
        if the removal was succesful
        """

    def add_content(id, sets, record_data, meta_data, assets_data):
        """Add content to the database, supplying an id and 3 dictionaries,
        of data. The dictionaries should contain at least the keys that
        are needed for generating the get_record, get_metadata and get_keys
        requests.
        Returns a boolean to indicate if the insertion was succesful
        """

    def add_set(id, name, description=None):
        """Add a set to the database
        Returns a boolean to indicate if the insertion was succesful
        """

    def remove_set(id):
        """Remove set from the database
        Returns a boolean to indicate if the removal was succesful
        """

    def empty_database():
        """Removes all data from the database, but doesn't remove the 
        table structures. Mainly used for testing.
        """

        
class IFeedConfig(Interface):

    id = Attribute(u"Id of the OAI Server instance")
    name = Attribute(u"Name of this OAI Server instance (for identify)")
    url = Attribute(u"Base URL of the OAI Server (for identify)")
    log = Attribute(u"Logger instance that logs activity and errors")
    admins = Attribute(u"List of email addresses that can be contacted, "
                      "for questions about the feed")
    metadata_prefixes = Attribute(
        u"List of metadataPrefixes this server can handle"
        "by default the list has 'oai_dc' included")
                   
    # some filter attributes

    content_type = Attribute(u"Type of content objects being served")
    scope = Attribute(u"Only serve objects with a specific (or lower) scope")
    sets_allowed = Attribute(u"Objects served must have one of these sets")
    sets_disallowed = Attribute(
        u"Objects served must not have one of these sets")
    filter_sets = Attribute(
        u"Objects served must have one of these sets, besides the "
        "conforming to the (dis-)allowed sets")
    sets_deleted = Attribute(
        u"Records in this set will always be served as deleted OAI records "
        "this can be used as an alternative to sets_dissallowed.")
    delay = Attribute(u"number of miliseconds to delay the feed")


    def get_oai_id(internal_id):
        """Rename internal id into oai_id"""

    def get_internal_id(oai_id):
        """Rename oai_id into internal id"""

    def get_setspec_id(internal_set_id):
        """Rename internal set id into a setspec id"""

    def get_internal_set_id(oai_setspec_id):
        """Rename setspec id into  internal set id"""

    def get_asset_path(internal_id, asset):
        """Return an absolute path to an asset given
        an internal id the asset data dict containing
        filename, md5, url and metadata
        """

class IServerRequest(Interface):

    def url():
        """Return the current url
        """

    def redirect(url):
        """Redirect to this url
        """

    def send_file(path):
        """Send the file located at 'path' back to the user
        """

    def query_dict():
        """Return a dictionary with QueryString values of the
        request
        """

    def write(data, mimetype):
        """Write data back to the client
        """

    def send_status(code, msg='', mimetype='text/plain'):
        """Return a status code to the user
        """

class IServer(Interface):

    def add_config(config):
        """Add a ServerConfig to the server
        """

    def get_config(id):
        """Get a ServerConfig by id
        """
    
    def download_asset(req, url, config):
        """Download an asset from a url
        """
    
    def allow_download(url, config):
        """Is user allowed to download this asset (returns bool)
        """

    def is_asset_url(url, config):
        """Is this url pointing to an asset (returns bool)
        """
            
    def handle_request(req):
        """Serve this request this method goes through the following steps:
        1. check if url is valid
        2. try to get ServerConfig for this url
        3. test if this is an asset url, if so check if download is allowed,
           and download asset
        4. if not asset url, get the oai server through the OAIServerFactory
        5. call the handleRequest method on the oai server, and return the result
        """
