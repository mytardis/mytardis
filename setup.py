import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'docs/changes.rst')).read()

setup(
    name="MyTardis",
    version="3.5",
    url='http://github.com/mytardis/mytardis',
    license='BSD',
    description="Next iteration of the TARDIS framework. No digital " +
        "repository required. Federated web stores + ftp access instead.",
    long_description=README + '\n\n' + CHANGES,
    author='Steve Androulakis',
    author_email='steve.androulakis@monash.edu',
    packages=find_packages(),
    namespace_packages=['tardis'],
    install_requires=[
        'lxml==3.2.1',
        'pyparsing==1.5.7',  # held back by rdflib and rdfextras
        'feedparser==5.1.3',
        'elementtree',
        'django==1.5.5',
        'django-registration==1.0',
        'django-extensions==1.1.1',
        'django-form-utils==0.2.0',
        'django-haystack==1.2.7',
        'django-bootstrap-form==2.0.6',
        'celery>=3.0.21',           # Delayed tasks and queues
        'django-celery>=3.0.17',
        'pysolr==2.1.0-beta',
        'beautifulsoup4==4.2.1',
        'south==0.8.1',
        'httplib2==0.8',
        'python-magic',  # File type detection
        'pytz==2013b',         # Timezone library
        'iso8601==0.1.4',      # ISO8601 time formatting
        'pyoai==2.4.4',        # For OAI-PMH provider
        'Wand==0.3.2',    # For image file conversion
        'django-mustachejs==0.6.0',  # client-side Mustache template helpers
        'pystache==0.5.3',  # For server-side Mustache rendering to aid SEO
        'rdflib==4.0.1',    # For ANZSRCO parsing for ANZSRC FoR codes
        'rdfextras==0.4',  # For parsing n3 ANZSRCO
        'django-user-agents==0.2.2',  # For user agent sensing
        'user-agents==0.1.1',
        'ua-parser==0.3.3',
        'PyYAML==3.10',
        'django-tastypie==0.9.16-tzfix',
        'bleach',
        # 'pygraphviz',  # for automatic diagram generation for the docs
        'paramiko',
        'jwt',
        'pwgen',
    ],
    dependency_links=[
        'https://github.com/grischa/django-tastypie/tarball/testing-mytardis-deployment#egg=django-tastypie-0.9.16-tzfix',  # noqa
    ]
)
