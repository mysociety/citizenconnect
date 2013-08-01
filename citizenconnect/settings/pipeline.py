from .paths import PARENT_DIR

# Processes static files when collectstatic is called, also versions
# them in the url.
#
# See http://django-pipeline.readthedocs.org/en/latest/storages.html
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# If you need to test out the pipeline in development, run
# `./manage.py collectstatic`, then uncomment this line.
#
# PIPELINE_ENABLED = True

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'
PIPELINE_SASS_BINARY = PARENT_DIR + '/gem-bin/sass'
PIPELINE_TEMPLATE_FUNC = '_.template'
PIPELINE_DISABLE_WRAPPER = True

PIPELINE_COMPILERS = (
  'pipeline.compilers.sass.SASSCompiler',
)

PIPELINE_CSS = {
    'default': {
        'source_filenames': (
            'css/leaflet.css',
            'css/placeholder_polyfill.min.css',
            'sass/default.scss',
            'css/select2/select2.css',
            'css/fancybox/jquery.fancybox-1.3.4.css',
            'css/rateit/rateit.css',
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
            'js/jquery.onfontresize.js',
            'js/placeholder_polyfill.jquery.js',
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
            'js/templates/*-filters.jst',
            'js/summary-table.js',
        ),
        'output_filename': 'js/summary-table.min.js'
    },
    'review_form': {
        'source_filenames': (
            # Note that the ordering here is important: review-form needs to be before rateit
            'js/review-form.js',
            'js/jquery.rateit.js',
        ),
        'output_filename': 'js/review-form.min.js'
    },
}
