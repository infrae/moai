from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='MOAI',
    version='1.1.0',
    author='Infrae',
    author_email='jasper@infrae.com',
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
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe=False,
    license='BSD',
    entry_points= {
    'console_scripts': [
    'update_database = moai.tools:update_database',
    'start_development_server = moai.tools:start_development_server',
    'generate_modpython_config = moai.http.apache:generate_config'
      ]
    },
    install_requires=[
    'pyoai>=2.4',
    'martian',
    'sqlalchemy',
    'simplejson'
    ],
)
