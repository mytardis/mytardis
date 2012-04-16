import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'docs/changes.rst')).read()

setup(
    name="MyTardis",
    version="2.5",
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
        'django==1.3',
        'django-registration',
        'django-extensions',
        'django-form-utils',
        'django-haystack',
        'pysolr',
        'beautifulsoup',
        'south',
        'django-celery',
        'django-kombu',
        'pytz',
        'httplib2',
        ],
)
