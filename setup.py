from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='MOAI',
    version='2.0.0',
    author='Infrae',
    author_email='info@infrae.com',
    url='http://infrae.com/products/moai',
    description="MOAI, A Open Access Server Platform for Institutional Repositories",
    long_description=(open(join(dirname(__file__), 'ABOUT.txt')).read()+
                      '\n'+
                      open(join(dirname(__file__), 'README.txt')).read()+
                      '\n'+
                      open(join(dirname(__file__), 'HISTORY.txt')).read()),
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Programming Language :: Python",
                 "License :: OSI Approved :: BSD License",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    packages=find_packages(),
    include_package_data = True,
    zip_safe=False,
    license='BSD',
    entry_points= {
    'console_scripts': [
        'update_moai = moai.tools:update_moai',
      ],
    'paste.app_factory':[
        'main=moai.wsgi:app_factory'
     ],
    'moai.content':[
        'moai_example=moai.example:ExampleContent'
     ],
    'moai.database':[
        'sqlite=moai.database:SQLDatabase',
        'mysql=moai.database:SQLDatabase',
        'postgres=moai.database:SQLDatabase',
        'oracle=moai.database:SQLDatabase'],
    'moai.provider':[
        'file=moai.provider.file:FileBasedContentProvider',
        'list=moai.provider.list:ListBasedContentProvider',
        'oai=moai.provider.oai:OAIBasedContentProvider',
        'fedora=moai.provider.feadora:FedoraBasedContentProvider'
     ],
    'moai.format':[
         'oai_dc=moai.metadata.oaidc:OAIDC',
         'mods=moai.metadata.mods:MODS',
         'nl_mods=moai.metadata.mods:NL_MODS',
         'didl=moai.metadata.didl:DIDL',
         'nl_didl=moai.metadata.dare_didl:DareDIDL'
     ],
    },
    install_requires=[
    'pyoai',
    'WSGIUtils',
    'wsgi_intercept',
    'webob',
    'paste',
    'pasteDeploy',
    'pasteScript',
    'sqlalchemy',
    ],
    test_suite='moai.test.suite'
)


