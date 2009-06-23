import martian

class ConfigurationProfile(object):
    """Subclass this to create custom profiles.
    use the name directive so it will be automaticly
    registered in the framework:

    class MyConfiguration(ConfigurationProfile):
        name('my_configuration')
        
    """
    martian.baseclass()

    def __init__(self, log, config):
        self.log = log
        self.config = config

    def get_content_provider(self):
        raise NotImplementedError

    def get_content_object(self):
        raise NotImplementedError
        
    def get_database_updater(self):
        raise NotImplementedError

    def get_database(self):
        raise NotImplementedError

    def get_server(self):
        raise NotImplementedError

    def start_server(self):
        raise NotImplementedError

class Plugin(object):
    """Create you're own plugins by subclassing this
    and specifying a moai.name.
    The plugin is executed after the database was updated'
    """
    martian.baseclass()
    def __init__(self, database, config=None):
        """Execute the plugin, with the new database.
        an optional config dictionary is used,
        if config values for this plugin were added in the buildout.cfg file
        """
        pass
    
    def run(self, updated_ids):
        """Do something with the list of updated ids
        """
    
class MetaDataFormat(object):
    martian.baseclass()

    def get_namespace(self):
        return self.ns[self.prefix]
    
    def get_schema_location(self):
        return self.schemas[self.prefix]


class name(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    
