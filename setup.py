from setuptools import setup, find_packages

setup(
    name = "tardis",
    version = "1.0",
    url = 'http://code.google.com/p/mytardis/',
    license = 'BSD',
    description = "Next iteration of the TARDIS framework. No digital repository required. Federated web stores + ftp access instead.",
    author = 'Steve Androulakis',
    author_email='steve.androulakis@monash.edu',
    packages=find_packages(),
    namespace_packages=['tardis'],
    install_requires = [
        'setuptools',
        'lxml',
        'feedparser',
        'django-registration',
        'django_extensions',
        'suds',
        'python-ldap',
        ],
)
