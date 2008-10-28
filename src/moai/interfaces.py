from zope.interface import Interface, Attribute

class IContentProvider(Interface):
    """Object that provides the content used to build the database
    that is used to serve the actual oai data
    """
    
    def update(from_date):
        """Harvests, new content added since from_date
        returns a list of content_ids that were changed/added
        """
        pass

    def count():
        """Returns number of content objects in the repository
        """

    def get_content():
        """Returns a list (or generator) of content objects.
        """

    def get_content_by_id(id):
        """Return a content object associated with a specific id
        """
        pass


    def get_sets():
        """Returns a list (or generator) of content sets.
        """

    def get_sets_by_id(id):
        """Return a content set associated with a specific id
        """
        pass


    
class IContentObject(Interface):

    id = Attribute(u"Id of the content object")
    content_type = Attribute(u"Type of the content object")
    when_modified = Attribute(u"Modification date of the object")
    deleted = Attribute(u"Boolean that tells if object is deleted or not")
    scope = Attribute(u'String indicating how public data is'
                      '(public/internal/private) if not present scope'
                      '"public" is assumed')
    sets = Attribute(u"A list of ids from sets that this object belongs to")
    
    # we also need to store the provider, since it can be needed when
    # validating the object relations
    provider = Attribute(u"The content provider that returned this object")

    def field_names():
        """Return a list of field names, used in this object
        """
        pass

    def relation_names():
        """Return a list of relation names, used in this object
        """
        
    def get_values(field_name):
        """Return a list of python objects (string/int/etc)
        from a specific field name
        """
        pass

    def get_relations(relation_name):
        """Return a list of tuples containing id/type strings
        of other content objects
        """   

        
class IContentSet(Interface):

    id = Attribute(u"Id of the set")
    name = Attribute(u"Name of the set")
    description = Attribute(u"Descriptive text of the set")
    when_modified = Attribute(u"Modification date of the object")

    provider = Attribute(u"The content provider that returned this object")

        
class IContentValidator(Interface):

    content_type = Attribute("The type of objects this validator can validate")

    def set_logger(logger_instance):
       """Make the validator use a specific custom logger
       (will probably be set automaticly in __init__)
       """
       pass
   
    def validate_object(content_object):
        """Validates an object, return a Boolean to indicate validity,
        Alle warnings and errors, should also be logged with the log object
        that's provided as an argument of the set_logger method
        """
        pass
    
class IDatabaseUpdater(Interface):

    def set_database(database):
        """Make the updater use a specific (new) database
        (will probably be set automaticly in __init__)
        """
        pass

    def set_content_provider(content_provider):
        """Make the updater use a specific ContentProvider
        (will probably be set automaticly in __init__)
        """
        pass

    def set_logger(logger_instance):
       """Make the updater use a specific custom logger
       (will probably be set automaticly in __init__)
       """
       pass

    def update(validate=True):
        """Update the database with the content_provider
        this will update the content_provider, optionally
        validate the content objects, and add everything
        to the database. This method returns a Database object
        if the update was succesful, otherwise None will be
        returned. Detailed progress information and
        error messages can be obtained by looking at the logging data
        """
        pass


class IDatabase(Interface):

    def oai_sets(offset=0, batch_size=20):
        """Used by queries from the OAI server. Format returned should be the
        following:

        [{'id': <string>,
          'name': <string>,
          'description': <string>}]
          
        """
        pass
    
    def oai_query(offset=0,
                  batch_size=20,
                  sets=[],
                  not_sets=[],
                  filter_sets=[],
                  from_date=None,
                  until_date=None):
        """Used by queries from the OAI server. Format returned should be the
        following:

        [{'record': <dict similar to get_record() output>,
          'metadata': <dict similar to get_metadata() output>,
          'assets': <dict similar to get_assets() output>}
        ]
        """
        pass
    
    def get_record(id):
        """Returns a dictionary of data that is available from the
        object with the specific id. The dictionary should contain at least
        the following data:

        {'identifier': unicode,
        'when_modified': dateTime,
        'deleted': boolean,
        'content_type': string,
        'sets': list of strings,
        'scope': string,
        }

        If the id does not exist, None will be returned
        """
        pass

    def get_metadata(id):
        """Returns a dictionary with additional data.
        Keys are always a string, values are always lists of python
        objects.

        If the id does not exist, None will be returned
        """
        pass

    def get_assets(id):
        """Returns a list with dictionaries describing the assets.
        The dictionaries should at least contain the following values:

        {filename: string,
         scope: string
        }
        """
        pass

    def get_set(id):
        """Returns a dictionary with set metadata,
        this also contains all the instances that are part of a certain
        class:

        {id: string,
         name: string,
         description: string (optional),
         content: list of content ids}
        """
        pass

    def remove_content(id):
        """Remove all the content of a given id, returns a boolean to indicate
        if the removal was succesful
        """
        pass

    def add_content(id, sets, record_data, meta_data, assets_data):
        """Add content to the database, supplying an id and 3 dictionaries,
        of data. The dictionaries should contain at least the keys that
        are needed for generating the get_record, get_metadata and get_keys
        requests.
        Returns a boolean to indicate if the insertion was succesful
        """
        pass

    def add_set(id, name, description):
        """Add a set to the database
        Returns a boolean to indicate if the insertion was succesful
        """

    def remove_set(id):
        """Remove set from the database
        Returns a boolean to indicate if the removal was succesful
        """

        
class IServerConfig(Interface):

    name = Attribute(u"Name of this OAI Server instance")
    admins = Attribute(u"List of email addresses that can be contacted, "
                      "for questions about the feed")

    # some filter attributes

    content_type = Attribute(u"Type of content objects being served")
    scope = Attribute(u"Only serve objects with a specific (or lower) scope")
    sets_allowed = Attribute(u"Objects served must have one of these sets")
    sets_disallowed = Attribute(
        u"Objects served must not have one of these sets")
    filter_sets = Attribute(
        u"Objects served must have one of these sets, besides the"
        "conforming to the (dis-)allowed sets")
    delay = Attribute(u"number of miliseconds to delay the feed")
    must_have_assets = Attribute(u"Objects can not be metadata_only")
        

class IServerBackend(Interface):

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

    


    

    
