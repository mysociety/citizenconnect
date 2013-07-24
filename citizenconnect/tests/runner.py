# Create a test runner that will only run the local tests and not the Django
# ones.
#
# based on http://stackoverflow.com/a/8194302/5349
import os
import tempfile
import shutil

from django.test.simple import DjangoTestSuiteRunner
from django.conf import settings
from django.contrib.sites.models import Site


class AppsTestSuiteRunner(DjangoTestSuiteRunner):
    """ Override the default django 'test' command, include only
        apps that are part of this project
        (unless the apps are specified explicitly)
    """

    def run_tests(self, test_labels, extra_tests=None, **kwargs):

        # If user has not specified the test to run go through all the apps and
        # filter out ones that should be skipped.
        if not test_labels:
            test_labels = []
            for app in settings.INSTALLED_APPS:
                if app.startswith('django') or app in settings.IGNORE_APPS_FOR_TESTING:
                    print "Skipping tests for %s" % app
                    continue
                test_labels.append(app)
        return super(AppsTestSuiteRunner, self).run_tests(
            test_labels, extra_tests, **kwargs
        )

    def run_suite(self, *args, **kwargs):

        # Change the site url to be 'testserver', so that the tests continue to
        # work as FullyQualifiedRedirectMiddleware will rewrite the urls to what
        # is expected by the default test client.
        Site.objects.update(name="testserver", domain="testserver")

        return super(AppsTestSuiteRunner, self).run_suite(*args, **kwargs)

    def setup_test_environment(self):
        super(AppsTestSuiteRunner, self).setup_test_environment()
        # Change media root to be a temp directory
        settings.MEDIA_ROOT = tempfile.mkdtemp()

    def teardown_test_environment(self):
        super(AppsTestSuiteRunner, self).teardown_test_environment
        if(os.path.exists(settings.MEDIA_ROOT)):
            shutil.rmtree(settings.MEDIA_ROOT)
