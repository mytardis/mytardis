import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'docs/changes.rst')).read()

setup(
    name="MyTardis",
    version="3.0.0-alpha1",
    url='http://github.com/mytardis/mytardis',
    license='BSD',
    description="Next iteration of the TARDIS framework. No digital " + \
        "repository required. Federated web stores + ftp access instead.",
    long_description=README + '\n\n' + CHANGES,
    author='Steve Androulakis',
    author_email='steve.androulakis@monash.edu',
    packages=find_packages(),
    namespace_packages=['tardis'],
    install_requires=[
        'setuptools',
        'lxml',
        'feedparser',
        'elementtree',
        'django==1.4.1',
        'django-registration',
        'django-extensions',
        'django-form-utils',
        'django-haystack',
        'django-bootstrap-form',
        'celery',           # Delayed tasks and queues
        'django-celery',
        'django-kombu',
        'pysolr',
        'beautifulsoup4',
        'south',
        'httplib2',
        'python-magic', # File type detection
        'pytz',         # Timezone library
        'iso8601',      # ISO8601 time formatting
        'pyoai',        # For OAI-PMH provider
        'Wand==0.1.10',    # For image file conversion
        'django-mustachejs', # For client-side Mustache template helpers
        'pystache', # For server-side Mustache rendering to aid SEO
        'rdflib',    # For ANZSRCO parsing for ANZSRC FoR codes
        'rdfextras', # For parsing n3 ANZSRCO
        ],
    dependency_links = [
        'https://github.com/dahlia/wand/tarball/warning-bugfix#egg=Wand-0.1.10',
        'https://github.com/defunkt/pystache/tarball/v0.5.2#egg=pystache-0.5.2'
    ]
)
