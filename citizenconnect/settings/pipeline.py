STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_COMPILERS = (
  'pipeline.compilers.sass.SASSCompiler',
)

PIPELINE_CSS = {
    'default': {
        'source_filenames': (
            'css/leaflet.css',
            'css/placeholder_polyfill.min.css',
            'sass/default.scss',
        ),
        'output_filename': 'css/default.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

PIPELINE_JS = {
    'frameworks': {
        'source_filenames': (
            'js/jquery-1.10.2.js',
            'js/placeholder_polyfill.jquery.min.combo.js',
            'js/jquery.customSelect.js',
        ),
        'output_filename': 'js/frameworks.js',
    },
    'careconnect': {
        'source_filenames': (
            'js/tables.js',
            'js/filters.js',
        ),
        'output_filename': 'js/careconnect.js'
    },
}
