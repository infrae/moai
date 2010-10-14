from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='MOAI',
    version='2.0.0dev',
    author='Infrae',
    author_email='info@infrae.com',
    url='http://moai.infrae.com',
    description="MOAI, A Open Access Server Platform for Institutional Repositories",
    long_description=(open(join(dirname(__file__), 'README.txt')).read()+
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
    'moai.provider':[
        'file=moai.provider.file:FileBasedContentProvider',
        'list=moai.provider.list:ListBasedContentProvider',
        'oai=moai.provider.oai:OAIBasedContentProvider',
        'fedora=moai.provider.feadora:FedoraBasedContentProvider'
     ],
    'moai.format':[
         'oai_dc=moai.metadata:OAIDC',
         'mods=moai.metadata:MODS'
     ],
    },
    install_requires=[
    'pyoai',
    'WSGIUtils',
    'wsgi_intercept',
    'webob',
    'pasteScript',
    'sqlalchemy',
    'simplejson'
    ],
    test_suite='moai.test.suite'
)


