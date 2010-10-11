import sys

class ContentError(Exception):
    def __init__(self, contentclass, input):
        err, detail, tb = sys.exc_info()
        self.err= err
        self.detail = detail
        self.tb = tb
        self.contentclass = contentclass
        self.input = input
        
    def logmessage(self):
        return 'Can not create %s: %s \n         %s\n         %s' % (
            self.contentclass.__name__,
            self.err.__name__,
            self.detail,
            self.input)

class DatabaseError(Exception):
    def __init__(self, id, add_type):
        err, detail, tb = sys.exc_info()
        self.err= err
        self.detail = detail
        self.tb = tb
        self.id = id
        self.add_type = add_type
    def logmessage(self):
        return 'Can not add %s "%s" to database: %s\n         %s' % (
            self.add_type,
            self.id,
            self.err.__name__,
            self.detail)
    
class UnknownRecordID(Exception):
    pass
