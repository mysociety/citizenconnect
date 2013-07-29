from .paths import PARENT_DIR


PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'
PIPELINE_SASS_BINARY = PARENT_DIR + '/gem-bin/sass'
PIPELINE_TEMPLATE_FUNC = '_.template'

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
            'css/fancybox/jquery.fancybox-1.3.4.css',
            'css/rateit/rateit.css',
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
            'js/underscore.js',

            # TODO: Find an uncompressed version as this won't minify well (because it's already minified).
            'js/placeholder_polyfill.jquery.min.combo.js',
            'js/jquery.customSelect.js',
            'js/select2.js',
            'js/jquery.browser.js',
            'js/jquery.fancybox-1.3.4.js',
            'js/fancybox-zoom.js',
            'js/tables.js',
            'js/filters.js',
        ),
        'output_filename': 'js/careconnect.min.js'
    },
    'map': {
        'source_filenames': (
            'js/leaflet-src.js',
            'js/wax.leaf.js',
            'js/oms.js',
            'js/spin.js',
            'js/jquery.spin.js',
            'js/templates/map-hover-bubble.jst',
            'js/map.js',
        ),
        'output_filename': 'js/map.min.js'
    },
    'about': {
        'source_filenames': (
            'js/jquery.scrollspy.js',
            'js/side_nav.js',
            'js/about.js',
        ),
        'output_filename': 'js/about.min.js'
    },
    'problem_form': {
        'source_filenames': (
            'js/problem-form.js',
        ),
        'output_filename': 'js/problem-form.min.js'
    },
    'survey_form': {
        'source_filenames': (
            'js/survey_form.js',
        ),
        'output_filename': 'js/survey_form.min.js'
    },
    'moderation_form': {
        'source_filenames': (
            'js/moderation_form.js',
        ),
        'output_filename': 'js/moderation_form.min.js'
    },
    'summary_table': {
        'source_filenames': (
            'js/summary-table.js',
        ),
        'output_filename': 'js/summary-table.min.js'
    },
}
