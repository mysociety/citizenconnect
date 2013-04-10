# Create a test runner that will only run the local tests and not the Django
# ones.
#
# based on http://stackoverflow.com/a/8194302/5349

from django.test.simple import DjangoTestSuiteRunner
from django.conf import settings

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