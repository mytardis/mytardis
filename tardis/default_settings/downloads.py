ARCHIVE_FILE_MAPPERS = {
    'deep-storage': (
        'tardis.apps.deep_storage_download_mapper.mapper.deep_storage_mapper',
    ),
}

# Site's default archive organization (i.e. path structure)
DEFAULT_ARCHIVE_ORGANIZATION = 'deep-storage'

DEFAULT_ARCHIVE_FORMATS = ['tar']
'''
Site's preferred archive types, with the most preferred first
other available option: 'tgz'. Add to list if desired
'''
