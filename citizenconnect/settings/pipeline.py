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

# Compress the css and js using yui-compressor.
PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'

# On some platforms this might be called "yuicompressor", so it may be
# necessary to symlink it into your PATH as "yui-compressor".
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'

# Specify path to local sass version.
PIPELINE_SASS_BINARY = PARENT_DIR + '/gem-bin/sass'

# Use underscore's templating library for javascript templates. These
# templates get compiled into the javascript in production.
PIPELINE_TEMPLATE_FUNC = '_.template'

# Don't use a top-level function safety wrapper.
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
            'js/jquery.scrollspy.js',
            'js/side_nav.js',
            'js/tables.js',
            'js/filters.js',
            'js/templates/*.jst',
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
            'js/map.js',
        ),
        'output_filename': 'js/map.min.js'
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
    'review_form': {
        'source_filenames': (
            # Note that the ordering here is important: review-form needs to be before rateit
            'js/review-form.js',
            'js/jquery.rateit.js',
        ),
        'output_filename': 'js/review-form.min.js'
    },
    'live_feed': {
        'source_filenames': (
            'js/live-feed.js',
        ),
        'output_filename': 'js/live-feed.min.js'
    },
}
