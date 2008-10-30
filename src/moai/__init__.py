import martian

class ConfigurationProfile(object):

    martian.baseclass()

    def __init__(self, log):
        self.log = log

    def providerFactory(self):
        raise NotImplementedError

    def serverFactory(self):
        raise NotImplementedError

    def databaseFactory(self):
        raise NotImplementedError

    def contentProviderFactory(self):
        raise NotImplementedError
        
    def requestFactory(self):
        raise NotImplementedError

class MataDataPrefix(object):
    martian.baseclass()

class name(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    
