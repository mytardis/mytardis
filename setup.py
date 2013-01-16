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
        'lxml==2.2.7',
        'pyparsing==1.5.6',
        'feedparser==5.1.2',
        'elementtree',
        'django==1.4.1',
        'django-registration==0.8',
        'django-extensions==0.9',
        'django-form-utils==0.2.0',
        'django-haystack==1.2.7',
        'django-bootstrap-form==2.0.3',
        'celery==2.5.5',           # Delayed tasks and queues
        'django-celery==2.5.5',
        'django-kombu==0.9.4',
        'pysolr==2.1.0-beta',
        'beautifulsoup4==4.1.1',
        'south==0.7.6',
        'httplib2==0.7.6',
        'python-magic==0.4.0dev',  # File type detection
        'pytz==2012d',         # Timezone library
        'iso8601==0.1.4',      # ISO8601 time formatting
        'pyoai==2.4.4',        # For OAI-PMH provider
        'Wand==0.1.10',    # For image file conversion
        'django-mustachejs==0.6.0',  # client-side Mustache template helpers
        'pystache==0.5.2',  # For server-side Mustache rendering to aid SEO
        'rdflib==3.2.1',    # For ANZSRCO parsing for ANZSRC FoR codes
        'rdfextras==0.2',  # For parsing n3 ANZSRCO
        ],
    dependency_links = [
        'https://github.com/dahlia/wand/tarball/warning-bugfix#egg=Wand-0.1.10',
        'https://github.com/UQ-CMM-Mirage/django-celery/tarball/2.5#egg=django-celery-2.5.5',
        'https://github.com/defunkt/pystache/tarball/v0.5.2#egg=pystache-0.5.2',
        'https://github.com/russell/python-magic/tarball/master#egg=python-magic-0.4.0dev',
    ]
)
