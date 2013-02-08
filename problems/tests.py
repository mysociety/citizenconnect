from django.test import TestCase

from .models import Problem

class ProblemTests(TestCase):

    reset_sequences = True

    def test_problem_form_exists(self):
        resp = self.client.get('/choices/problem/problem-form/gppractices/12702')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Report your problem' in resp.content)

    def test_problem_form_happy_path(self):
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', {
            'organisation_type': 'gppractices',
            'choices_id': 12702,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': '1',
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': '0'
        })
        self.assertRedirects(resp, '/choices/problem/problem-confirm')
        # Check in db
        problem = Problem.objects.get(reporter_name='1')
        self.assertEqual(problem.organisation_type, 'gppractices')
        self.assertEqual(problem.choices_id, 12702)
        self.assertEqual(problem.public, False)
        self.assertEqual(problem.public_reporter_name, False)
        self.assertEqual(problem.description, 'This is a problem')
        self.assertEqual(problem.reporter_name, '1')
        self.assertEqual(problem.reporter_email, 'steve@mysociety.org')

    def test_problem_form_respects_name_privacy(self):
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', {
            'organisation_type': 'gppractices',
            'choices_id': 12702,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': '2',
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': '1'
        })
        # Check in db
        problem = Problem.objects.get(reporter_name='2')
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, False)

    def test_problem_form_respects_public_privacy(self):
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', {
            'organisation_type': 'gppractices',
            'choices_id': 12702,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': '2',
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': '2'
        })
        # Check in db
        problem = Problem.objects.get(reporter_name='2')
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, True)