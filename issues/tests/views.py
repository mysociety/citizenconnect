from django.test import TestCase
from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse

from sorl.thumbnail import get_thumbnail

from organisations.tests import (
    create_test_problem,
    create_test_organisation,
    create_test_service,
    create_review_with_age,
    create_problem_with_age,
    AuthorizationTestCase
)
from responses.models import ProblemResponse

from ..models import Problem, ProblemImage
from .lib import ProblemImageTestBase
from ..lib import int_to_base32


class ProblemPublicViewTests(ProblemImageTestBase, AuthorizationTestCase):

    def setUp(self):
        super(ProblemPublicViewTests, self).setUp()
        self.test_moderated_problem = create_test_problem({'organisation': self.test_hospital,
                                                           'publication_status': Problem.PUBLISHED,
                                                           'moderated_description': "A moderated description"})
        self.test_unmoderated_problem = create_test_problem({'organisation': self.test_hospital})
        self.test_private_problem = create_test_problem({'organisation': self.test_hospital,
                                                         'public': False,
                                                         'public_reporter_name': False,
                                                         'publication_status': Problem.PUBLISHED})

        self.test_moderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_moderated_problem.id,
                                                                          'cobrand': 'choices'})
        self.test_unmoderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_unmoderated_problem.id,
                                                                            'cobrand': 'choices'})
        self.test_private_problem_url = reverse('problem-view', kwargs={'pk': self.test_private_problem.id,
                                                                        'cobrand': 'choices'})

    def test_public_problem_page_exists(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, self.test_hospital.name, count=1, status_code=200)

    def test_public_problem_displays_responses(self):
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_moderated_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_moderated_problem)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_problem_displays_empty_response_message(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "No responses", count=1, status_code=200)

    def test_public_problem_accessible_to_everyone(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.trust_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.superuser)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_allowed_users(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_other_users_but_no_details_shown(self):
        # Set the private problem details to something explicit
        self.test_private_problem.description = "Private Problem description"
        # This wouldn't happen in real life, but it's best to check!
        self.test_private_problem.moderated_description = "Moderated Private Problem description"
        self.test_private_problem.reporter_name = "Jane Doe"
        self.test_private_problem.save()

        # Try as anon user
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, self.test_private_problem.description)
        self.assertNotContains(resp, self.test_private_problem.moderated_description)
        self.assertNotContains(resp, self.test_private_problem.reporter_name)

        for user in [self.gp_surgery_user, self.other_ccg_user]:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, self.test_private_problem.description)
            self.assertNotContains(resp, self.test_private_problem.moderated_description)
            self.assertNotContains(resp, self.test_private_problem.reporter_name)

    def test_private_problem_doesnt_show_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_private_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_private_problem)

        # Try as anon user
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, response1.response)
        self.assertNotContains(resp, response2.response)

        for user in [self.gp_surgery_user, self.other_ccg_user]:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, response1.response)
            self.assertNotContains(resp, response2.response)

    def test_private_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_accessible_to_everyone(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.client.logout()
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_unmoderated_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_doesnt_show_details(self):
        self.client.logout()
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertNotContains(resp, self.test_unmoderated_problem.description)
        self.assertNotContains(resp, self.test_unmoderated_problem.reporter_name)
        self.assertNotContains(resp, "Responses")

    def test_anon_user_sees_moderated_description_only(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, self.test_moderated_problem.description)
        self.assertContains(resp, self.test_moderated_problem.moderated_description)

    def test_shows_open_or_closed_and_specific_status(self):
        # An open problem
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "Open")
        self.assertContains(resp, self.test_moderated_problem.get_status_display())

        # A closed problem
        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': "A moderated description",
                                                   'status': Problem.RESOLVED})
        closed_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                             'pk': self.closed_problem.id})
        resp = self.client.get(closed_problem_url)
        self.assertContains(resp, "Closed")
        self.assertContains(resp, self.closed_problem.get_status_display())

    def test_doesnt_show_priority_on_public_pages(self):
        # A low priority problem - should never show priority
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, "Priority")

        # A high priority problem
        self.high_priority_problem = create_test_problem({'organisation': self.test_hospital,
                                                          'publication_status': Problem.PUBLISHED,
                                                          'moderated_description': "A moderated description",
                                                          'status': Problem.NEW,
                                                          'priority': Problem.PRIORITY_HIGH})
        high_priority_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                                    'pk': self.high_priority_problem.id})
        resp = self.client.get(high_priority_problem_url)
        self.assertNotContains(resp, "Priority")

    def test_doesnt_show_breach_on_public_pages(self):
        # A breach problem
        self.breach_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': "A moderated description",
                                                   'status': Problem.NEW,
                                                   'breach': True})
        breach_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                             'pk': self.breach_problem.id})
        resp = self.client.get(breach_problem_url)
        self.assertNotContains(resp, "Breach")

    def test_doesnt_show_publication_status_on_public_pages(self):
        # A published problem
        self.published_problem = create_test_problem({'organisation': self.test_hospital,
                                                      'publication_status': Problem.PUBLISHED,
                                                      'moderated_description': "A moderated description",
                                                      'status': Problem.NEW,
                                                      'publication_status': Problem.PUBLISHED})
        published_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                                'pk': self.published_problem.id})
        resp = self.client.get(published_problem_url)
        self.assertNotContains(resp, self.published_problem.get_publication_status_display())

    def test_doesnt_show_history_on_public_pages(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, "History")

    def test_shows_formal_complaint(self):
        self.test_moderated_problem.formal_complaint = True
        self.test_moderated_problem.save()
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, '<span class="icon-warning  meta-data-list__icon-red" aria-hidden="true"></span> Formal complaint')

    def test_shows_report_link(self):
        resp = self.client.get(self.test_moderated_problem_url)
        report_url = reverse('feedback', kwargs={'cobrand': 'choices'})
        expected_link = '<a href="{0}?problem_ref={1}">Report as unsuitable</a>'.format(report_url, self.test_moderated_problem.reference_number)
        self.assertContains(resp, expected_link)

    def test_images_shown(self):

        tests = (
            # problem, should_images_be_visible
            (self.test_moderated_problem,   True),
            (self.test_unmoderated_problem, False),
            (self.test_private_problem,     False),
        )

        image_geometry = "x70"

        for problem, should_images_be_visible in tests:

            # Add images to the public and private problems
            test_image = ImageFile(self.jpg)
            image = ProblemImage.objects.create(problem=problem, image=test_image)

            # setup
            problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'choices'})
            thumbnail_url = get_thumbnail(image.image, image_geometry).url
            img_tag = 'src="{0}"'.format(thumbnail_url)

            # Check that public problem has images on page
            resp = self.client.get(problem_url)

            if should_images_be_visible:
                self.assertContains(resp, img_tag, msg_prefix=str(problem))
            else:
                self.assertNotContains(resp, img_tag, msg_prefix=str(problem))


class ProblemProviderPickerTests(TestCase):

    def setUp(self):
        pick_provider_url = reverse('problems-pick-provider', kwargs={'cobrand': 'choices'})
        self.results_url = "{0}?organisation_type={1}&location={2}".format(pick_provider_url, 'gppractices', 'London')

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)


class ProblemSurveyTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemSurveyTests, self).setUp()
        self.test_problem = create_test_problem({'organisation': self.test_hospital})
        self.form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                        'response': 'n',
                                                        'id': int_to_base32(self.test_problem.id),
                                                        'token': self.test_problem.make_token(5555)})

    def test_form_page_exists(self):
        resp = self.client.get(self.form_page)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Thanks for your feedback', count=1, status_code=200)
        self.assertContains(resp, self.test_hospital.name, count=1)

    def test_form_page_returns_a_404_for_a_non_existent_problem(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'n',
                                                   'id': int_to_base32(-20),
                                                   'token': self.test_problem.make_token(5555)})
        resp = self.client.get(form_page)
        self.assertEqual(resp.status_code, 404)

    def test_form_page_records_the_happy_outcome_no_response(self):
        self.assertEqual(self.test_problem.happy_outcome, None)
        self.assertEqual(self.test_problem.happy_service, None)
        self.client.get(self.form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_outcome, False)
        self.assertEqual(test_problem.happy_service, None)

    def test_form_page_records_the_happy_outcome_yes_response(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'y',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.assertEqual(self.test_problem.happy_outcome, None)
        self.assertEqual(self.test_problem.happy_service, None)
        self.client.get(form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_outcome, True)

    def test_form_page_records_nothing_for_a_no_answer_response(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'd',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.assertEqual(self.test_problem.happy_outcome, None)
        self.assertEqual(self.test_problem.happy_service, None)
        resp = self.client.get(form_page)
        self.assertEqual(resp.status_code, 200)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_outcome, None)
        self.assertEqual(test_problem.happy_service, None)

    def test_confirm_page_links_to_reviews(self):
        # Now post to it to get the confirmation page
        resp = self.client.post(self.form_page, {})
        expected_review_url = reverse('review-form',
                                      kwargs={'cobrand': 'choices',
                                              'ods_code': self.test_hospital.ods_code})
        self.assertContains(resp, 'share your experience')
        self.assertContains(resp, expected_review_url)


class HomePageTests(TestCase):

    def setUp(self):
        self.homepage_url = reverse('home', kwargs={'cobrand': 'choices'})
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        public_atts = {'publication_status': Problem.PUBLISHED}
        # Some problems and reviews
        create_problem_with_age(self.test_organisation, age=1, attributes=public_atts)
        create_review_with_age(self.test_organisation, age=2)
        create_problem_with_age(self.test_organisation, age=4, attributes=public_atts)
        create_review_with_age(self.test_organisation, age=3)
        create_review_with_age(self.test_organisation, age=5)
        public_atts.update({'moderated_description': 'Sixth item'})
        create_problem_with_age(self.test_organisation, age=6, attributes=public_atts)

        unmoderated_problem = create_problem_with_age(
            self.test_organisation,
            age=1,
            attributes={'publication_status': Problem.NOT_MODERATED}
        )
        self.unmoderated_problem_url = reverse(
            'problem-view',
            kwargs={'cobrand': 'choices', 'pk': unmoderated_problem.pk}
        )

    def test_homepage_exists(self):
        resp = self.client.get(self.homepage_url)
        self.assertEqual(resp.status_code, 200)

    def test_displays_last_five_problems_or_reviews(self):
        resp = self.client.get(self.homepage_url)
        self.assertContains(resp, '<span class="feed-list__title">', count=5, status_code=200)
        self.assertNotContains(resp, 'Sixth item')

    def test_does_not_display_unmoderated_problems(self):
        resp = self.client.get(self.homepage_url)
        self.assertNotContains(resp, self.unmoderated_problem_url)


class PublicLookupFormTests(TestCase):

    def setUp(self):
        self.homepage_url = reverse('home', kwargs={'cobrand': 'choices'})
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_problem = create_test_problem({'organisation': self.test_organisation,
                                                 'publication_status': Problem.PUBLISHED})
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'status': Problem.RESOLVED})
        self.problem_url = reverse('problem-view', kwargs={'pk':self.test_problem.id,
                                                           'cobrand': 'choices'})
        self.closed_problem_url = reverse('problem-view', kwargs={'pk':self.closed_problem.id,
                                                                  'cobrand': 'choices'})

        self.problem_reference = '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)

    def test_happy_path(self):
        resp = self.client.post(self.homepage_url, {'reference_number': self.problem_reference})
        self.assertRedirects(resp, self.problem_url)

    def test_obvious_correction(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX.lower(), self.test_problem.id)})
        self.assertRedirects(resp, self.problem_url)

    def test_rejects_hidden_problems(self):
        self.test_problem.publication_status = Problem.REJECTED
        self.test_problem.save()
        resp = self.client.post(self.homepage_url, {'reference_number': self.problem_reference})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not available')

    def test_form_rejects_empty_submissions(self):
        resp = self.client.post(self.homepage_url, {})
        self.assertFormError(resp, 'form', 'reference_number', 'This field is required.')

    def test_form_rejects_unknown_prefixes(self):
        resp = self.client.post(self.homepage_url, {'reference_number': 'a123'})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_unknown_problems(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}12300'.format(Problem.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no problems with that reference number')

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, self.closed_problem_url)

    def test_form_handles_non_numeric_input(self):
        # Issues 1090 - Submitting just 'P' got you a 500 error, not a nice message
        for reference_number in ['P', 'ABC', 'PABC', 'P\-.=']:
            resp = self.client.post(
                self.homepage_url,
                {
                    'reference_number': reference_number
                }
            )
            self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')


class OrganisationProblemsTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationProblemsTests, self).setUp()

        # Organisations
        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123',
                                                  'parent': self.test_trust})
        self.clinic = create_test_organisation({'organisation_type': 'clinics',
                                                'ods_code': 'GHI123',
                                                'parent': self.test_trust})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456',
                                            'parent': self.test_gp_surgery})

        # Useful urls
        self.public_hospital_problems_url = reverse('public-org-problems',
                                                    kwargs={'ods_code': self.hospital.ods_code,
                                                            'cobrand': 'choices'})
        self.public_clinic_problems_url = reverse('public-org-problems',
                                                  kwargs={'ods_code': self.clinic.ods_code,
                                                          'cobrand': 'choices'})
        self.public_gp_problems_url = reverse('public-org-problems',
                                              kwargs={'ods_code': self.gp.ods_code,
                                                      'cobrand': 'choices'})

        # Problems
        self.staff_problem = create_test_problem({'category': 'staff',
                                                  'organisation': self.hospital,
                                                  'publication_status': Problem.PUBLISHED,
                                                  'moderated_description': "Moderated description"})
        # Add an explicitly public and an explicitly private problem to test
        # privacy is respected
        self.public_problem = create_test_problem({'organisation': self.hospital})
        self.private_problem = create_test_problem({'organisation': self.hospital, 'public': False})

    def test_shows_services_for_hospitals(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, '<th class="service">Department</th>', count=1, status_code=200)

    def test_shows_time_limits_for_hospitals(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>', count=1, status_code=200)
        self.assertContains(resp, '<th class="time_to_address">Close</th>', count=1, status_code=200)

    def test_shows_services_for_clinics(self):
        resp = self.client.get(self.public_clinic_problems_url)
        self.assertContains(resp, '<th class="service">Department</th>', count=1, status_code=200)

    def test_shows_time_limits_for_clinics(self):
        resp = self.client.get(self.public_clinic_problems_url)
        self.assertContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>', count=1, status_code=200)
        self.assertContains(resp, '<th class="time_to_address">Close</th>', count=1, status_code=200)

    def test_no_services_for_gps(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<th class="service">Department</th>')

    def test_no_time_limits_for_gps(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<th class="time_to_acknowledge">Acknowledge</th>')
        self.assertNotContains(resp, '<th class="time_to_address">Close</th>')

    def test_public_page_exists_and_is_accessible_to_anyone(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_page_links_to_public_problems(self):
        staff_problem_url = reverse('problem-view', kwargs={'pk': self.staff_problem.id,
                                                            'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertContains(resp, staff_problem_url)

    def test_public_page_shows_private_problems(self):
        # Add a private problem
        private_problem = create_test_problem({'organisation': self.hospital,
                                               'publication_status': Problem.PUBLISHED,
                                               'public': False})
        private_problem_url = reverse('problem-view', kwargs={'pk': self.private_problem.id,
                                                              'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(private_problem.reference_number in resp.content)
        self.assertTrue(private_problem.summary in resp.content)
        self.assertTrue(private_problem_url in resp.content)

    def test_public_page_doesnt_show_rejected_problems(self):
        # Add some problems which shouldn't show up
        rejected_problem = create_test_problem({'organisation': self.hospital,
                                                'publication_status': Problem.REJECTED})
        rejected_problem_url = reverse('problem-view', kwargs={'pk': rejected_problem.id,
                                                               'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(rejected_problem_url not in resp.content)

    def test_public_page_shows_not_moderated_problems(self):
        unmoderated_problem = create_test_problem({'organisation': self.hospital,
                                                   'publication_status': Problem.NOT_MODERATED})
        unmoderated_problem_url = reverse('problem-view', kwargs={'pk': unmoderated_problem.id,
                                                                  'cobrand': 'choices'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertTrue(unmoderated_problem_url in resp.content)

    def test_filters_by_status(self):
        # Add a problem in a different status that would show up
        resolved_problem = create_test_problem({'organisation': self.hospital,
                                                'status': Problem.ACKNOWLEDGED,
                                                'publication_status': Problem.PUBLISHED,
                                                'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.NEW)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        self.assertNotContains(resp, resolved_problem.reference_number)

    def test_shows_only_public_statuses_on_public_page(self):
        resp = self.client.get(self.public_hospital_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            if status in Problem.HIDDEN_STATUSES:
                self.assertNotContains(resp, '<option value="{0}">{1}</option>'.format(status, label))

    def test_ignores_private_statuses_on_public_page(self):
        # Even if we manually hack the url, it shouldn't do any filtering
        # Add a problem in a different status that would show up
        abusive_problem = create_test_problem({'organisation': self.hospital,
                                               'status': Problem.ABUSIVE,
                                               'publication_status': Problem.PUBLISHED,
                                               'moderated_description': 'Moderated'})
        status_filtered_url = "{0}?status={1}".format(self.public_hospital_problems_url, Problem.ABUSIVE)
        resp = self.client.get(status_filtered_url)
        self.assertContains(resp, self.staff_problem.reference_number)
        self.assertNotContains(resp, abusive_problem.reference_number)

    def test_filters_by_category(self):
        # Add a problem in a different status that would show up
        cleanliness_problem = create_test_problem({'organisation': self.hospital,
                                                   'category': 'cleanliness',
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': 'Moderated'})
        category_filtered_url = "{0}?category=cleanliness".format(self.public_hospital_problems_url)
        resp = self.client.get(category_filtered_url)
        self.assertContains(resp, cleanliness_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_public_page_does_not_have_breach_filter(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<option value="breach">')

    def test_public_page_does_not_have_formal_complaint_filter(self):
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<option value="formal_complaint">')

    def test_doesnt_show_service_filter_for_gp(self):
        resp = self.client.get(self.public_gp_problems_url)
        self.assertNotContains(resp, '<select name="service_id" id="id_service_id">')

    def test_filters_by_service_for_hospital(self):
        # Add a service to the test hospital
        service = create_test_service({'organisation': self.hospital})
        # Add a problem about a specific service
        service_problem = create_test_problem({'organisation': self.hospital,
                                               'service': service,
                                               'publication_status': Problem.PUBLISHED,
                                               'moderated_description': 'Moderated'})
        service_filtered_url = "{0}?service_id={1}".format(self.public_hospital_problems_url, service.id)
        resp = self.client.get(service_filtered_url)
        self.assertContains(resp, service_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_column_sorting(self):
        # Test that each of the columns we expect to be sortable, is.
        # ISSUE-498 - this raised a 500 on 'resolved' because resolved was not a model field
        columns = ('reference_number',
                   'created',
                   'status',
                   'resolved')
        for column in columns:
            sorted_url = "{0}?sort={1}".format(self.public_hospital_problems_url, column)
            resp = self.client.get(sorted_url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['table'].data.ordering, [column])

    def test_public_page_doesnt_highlight_priority_problems(self):
        # Add a priority problem
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'problem-table__highlight')

    def test_public_page_doesnt_show_breach_flag(self):
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_public_page_shows_public_summary(self):
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.public_hospital_problems_url)
        self.assertNotContains(resp, 'private description')
        self.assertContains(resp, 'public description')


class OrganisationParentProblemsTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationParentProblemsTests, self).setUp()

        # Organisations
        self.hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                  'ods_code': 'ABC123',
                                                  'parent': self.test_trust})
        self.gp = create_test_organisation({'organisation_type': 'gppractices',
                                            'ods_code': 'DEF456',
                                            'parent': self.test_gp_surgery})

        # Useful urls
        self.trust_problems_url = reverse('org-parent-problems',
                                          kwargs={'code': self.hospital.parent.code})
        self.other_trust_problems_url = reverse('org-parent-problems',
                                                kwargs={'code': self.gp.parent.code})

        # Problems
        self.staff_problem = create_test_problem({'category': 'staff',
                                                  'organisation': self.hospital,
                                                  'publication_status': Problem.PUBLISHED,
                                                  'moderated_description': "Moderated description"})
        # Add an explicitly public and an explicitly private problem to test
        # privacy is respected
        self.public_problem = create_test_problem({'organisation': self.hospital})
        self.private_problem = create_test_problem({'organisation': self.hospital, 'public': False})

    def test_private_page_exists(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_page_links_to_problems(self):
        self.login_as(self.trust_user)
        response_url = reverse('response-form', kwargs={'pk': self.staff_problem.id})
        resp = self.client.get(self.trust_problems_url)
        self.assertTrue(response_url in resp.content)

    def test_private_page_shows_hidden_private_and_unmoderated_problems(self):
        # Add some extra problems
        unmoderated_problem = create_test_problem({'organisation': self.hospital})
        unmoderated_response_url = reverse('response-form', kwargs={'pk': unmoderated_problem.id})
        hidden_problem = create_test_problem({'organisation': self.hospital,
                                              'publication_status': Problem.REJECTED})
        hidden_response_url = reverse('response-form', kwargs={'pk': hidden_problem.id})
        private_problem = create_test_problem({'organisation': self.hospital,
                                               'publication_status': Problem.PUBLISHED,
                                               'public': False})
        private_response_url = reverse('response-form', kwargs={'pk': self.private_problem.id})
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertTrue(unmoderated_response_url in resp.content)
        self.assertTrue(hidden_response_url in resp.content)
        self.assertTrue(private_response_url in resp.content)
        self.assertTrue(private_problem.private_summary in resp.content)

    def test_private_page_is_inaccessible_to_anon_users(self):
        expected_login_url = "{0}?next={1}".format(self.login_url, self.trust_problems_url)
        resp = self.client.get(self.trust_problems_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_pages_are_accessible_to_all_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.trust_problems_url)
            self.assertEqual(resp.status_code, 200)
            resp = self.client.get(self.other_trust_problems_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_page_is_inaccessible_to_other_providers(self):
        self.login_as(self.gp_surgery_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 403)
        self.login_as(self.trust_user)
        resp = self.client.get(self.other_trust_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_inaccessible_to_other_ccgs(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 403)
        self.login_as(self.ccg_user)
        resp = self.client.get(self.other_trust_problems_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_page_is_accessible_to_ccg(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertEqual(resp.status_code, 200)

    def test_shows_all_statuses_on_private_page(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.trust_problems_url)
        for status, label in Problem.STATUS_CHOICES:
            self.assertContains(resp, '<option value="{0}">{1}</option>'.format(status, label))

    def test_private_page_filters_by_breach(self):
        # Add a breach problem
        self.login_as(self.trust_user)
        breach_problem = create_test_problem({'organisation': self.hospital,
                                              'breach': True,
                                              'publication_status': Problem.PUBLISHED,
                                              'moderated_description': 'Moderated'})
        breach_filtered_url = "{0}?flags=breach".format(self.trust_problems_url)
        resp = self.client.get(breach_filtered_url)
        self.assertContains(resp, breach_problem.reference_number)
        self.assertNotContains(resp, self.staff_problem.reference_number)

    def test_private_page_highlights_priority_problems(self):
        # Add a priority problem
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'priority': Problem.PRIORITY_HIGH})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, 'problem-table__highlight')

    def test_private_page_shows_breach_flag(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'moderated_description': 'Moderated',
                             'breach': True})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_private_page_shows_private_summary(self):
        self.login_as(self.trust_user)
        create_test_problem({'organisation': self.hospital,
                             'publication_status': Problem.PUBLISHED,
                             'description': 'private description',
                             'moderated_description': 'public description'})
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, 'private description')
        self.assertNotContains(resp, 'public description')

    def test_private_page_includes_provider_name(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.trust_problems_url)
        self.assertContains(resp, '<th class="orderable provider_name sortable">')
        self.assertContains(resp, self.test_hospital.name)


class OrganisationParentBreachesTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationParentBreachesTests, self).setUp()
        self.breach_dashboard_url = reverse('org-parent-breaches', kwargs={'code': self.test_trust.code})
        self.org_breach_problem = create_test_problem({'organisation': self.test_hospital,
                                                       'breach': True})
        self.other_org_breach_problem = create_test_problem({'organisation': self.test_gp_branch,
                                                             'breach': True})
        self.org_problem = create_test_problem({'organisation': self.test_hospital})

    def test_dashboard_accessible_to_provider(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_is_inacessible_to_other_people(self):
        people_who_shouldnt_have_access = [
            self.no_trust_user,
            self.gp_surgery_user,
            self.second_tier_moderator,
            self.other_ccg_user
        ]

        for user in people_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.breach_dashboard_url)
            self.assertEqual(resp.status_code, 403, '{0} can access {1} when they shouldn\'t be able to'.format(user.username, self.breach_dashboard_url))

    def test_dashboard_only_shows_breach_problems(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, self.org_breach_problem.reference_number)
        self.assertNotContains(resp, self.org_problem.reference_number)

    def test_dashboard_shows_breach_flag(self):
        self.login_as(self.ccg_user)
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, '<div class="problem-table__flag__breach">b</div>')

    def test_dashboard_highlights_priority_problems(self):
        self.login_as(self.ccg_user)
        # Up the priority of the breach problem
        self.org_breach_problem.priority = Problem.PRIORITY_HIGH
        self.org_breach_problem.save()
        resp = self.client.get(self.breach_dashboard_url)
        self.assertContains(resp, 'problem-table__highlight')
