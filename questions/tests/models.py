from django.test import TestCase

from organisations.tests import create_test_instance

from ..models import Question

class QuestionModelTests(TestCase):

    def setUp(self):
        self.test_question = create_test_instance(Question, {})

    def test_has_prefix_property(self):
        self.assertEqual(Question.PREFIX, 'Q')
        self.assertEqual(self.test_question.PREFIX, 'Q')

    def test_has_reference_number_property(self):
        self.assertEqual(self.test_question.reference_number, 'Q{0}'.format(self.test_question.id))