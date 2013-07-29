from .paths import PROJECT_ROOT


PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'
PIPELINE_SASS_BINARY = PROJECT_ROOT + '/bin/sass'

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_COMPILERS = (
  'pipeline.compilers.sass.SASSCompiler',
)

PIPELINE_CSS = {
    'default': {
        'source_filenames': (
            'css/leaflet.css',
            'css/placeholder_polyfill.min.css',
            'css/select2/select2.css',
            'sass/default.scss',
        ),
        'output_filename': 'css/default.min.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

PIPELINE_JS = {
    'careconnect': {
        'source_filenames': (
            'js/jquery-1.10.2.js',

            # TODO: Find an uncompressed version as this won't minify well (because it's already minified).
            'js/placeholder_polyfill.jquery.min.combo.js',
            'js/jquery.customSelect.js',
            'js/tables.js',
            'js/filters.js',
        ),
        'output_filename': 'js/careconnect.min.js'
    },
}
