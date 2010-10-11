import unittest
import doctest
import datetime

FLAGS = doctest.NORMALIZE_WHITESPACE + doctest.ELLIPSIS
GLOBS = {'datetime':datetime}

def test_suite():

    suite = unittest.TestSuite()
    suite.addTests([
        doctest.DocFileSuite('README.txt',
                             package='moai',
                             globs=GLOBS,
                             optionflags=FLAGS),
        ])

    return suite

