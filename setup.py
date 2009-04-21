from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='MOAI',
    version='0.10',
    author='Infrae',
    author_email='jasper@infrae.com',
    description=open(join(dirname(__file__), 'README.txt')).read(),
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
    'pyoai',
    'martian',
    'sqlalchemy',
    'simplejson'
    ],
)
