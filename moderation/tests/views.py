from django.test import TestCase

class Viewtests(TestCase):

    def setUp(self):
        self.home_url = '/choices/moderate/'
        self.lookup_url = '/choices/moderate/lookup'
        self.problem_form_url = '/choices/moderate/problem/1'
        self.question_form_url = '/choices/moderate/question/1'
        self.confirm_url = '/choices/moderate/confirm'

    def test_home_view_exists(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, 200)

    def test_lookup_view_exists(self):
        resp = self.client.get(self.lookup_url)
        self.assertEqual(resp.status_code, 200)

    def test_form_views_exist(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(self.question_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_confirm_view_exists(self):
        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 200)
