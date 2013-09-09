from django.test import TestCase

from organisations.tests.lib import create_test_problem

from ..forms import ConcurrentFormMixin


class TestConcurrentForm(ConcurrentFormMixin):
    """A Test form class to use in testing the mixin"""
    def __init__(self, request=None, concurrency_model=None, *args, **kwargs):
        super(TestConcurrentForm, self).__init__(request=request, *args, **kwargs)
        self.concurrency_model = concurrency_model


class ConcurrentRequest(object):
    """Helper class to mock out a request"""

    session = {}

    def __init__(self, session, *args, **kwargs):
        super(ConcurrentRequest, self).__init__(*args, **kwargs)
        self.session = session



class ConcurrentFormMixinTest(TestCase):

    def test_handles_missing_version(self):
        # Create a problem to test with
        problem = create_test_problem({})
        # Create a dummy request to pass into the form that's missing a
        # version for our problem
        session = {
            'object_versions': []
        }
        request = ConcurrentRequest(session=session)
        self.form = TestConcurrentForm(request=request, concurrency_model=problem)

        self.assertFalse(self.form.concurrency_check())
