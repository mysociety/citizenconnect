import uuid

from django.test import TestCase
from django.test.utils import override_settings
from django.test.testcases import to_list
from django.core.urlresolvers import reverse
from django.conf import settings

from organisations.tests.lib import create_test_organisation, create_test_service, create_test_problem
from citizenconnect.browser_testing import SeleniumTestCase

from ..models import Problem
from ..forms import ProblemForm
from ..lib import int_to_base32

from .lib import ProblemImageTestBase


class ProblemCreateFormBase(object):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.other_organisation = create_test_organisation({'ods_code': '22222'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.other_service = create_test_service({'organisation': self.other_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = reverse('problem-form', kwargs={'ods_code': self.test_organisation.ods_code,
                                                        'cobrand': 'choices'})
        self.test_problem = {
            'organisation': self.test_organisation.id,
            'service': self.test_service.id,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': ProblemForm.PRIVACY_PRIVATE,
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'agree_to_terms': True,
            'elevate_priority': False,
            'website': '',  # honeypot - should be blank
            # Image formset fields
            'images-TOTAL_FORMS': 0,
            'images-INITIAL_FORMS': 0,
            'images-MAX_NUM_FORMS': 0,
        }


class ProblemCreateFormTests(ProblemCreateFormBase, TestCase):

    def test_problem_form_exists(self):
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Report your problem' in resp.content)

    def test_problem_form_shows_provider_name(self):
        resp = self.client.get(self.form_url)
        self.assertTrue(self.test_organisation.name in resp.content)

    @override_settings(SURVEY_INTERVAL_IN_DAYS=99)
    def test_problem_form_happy_path(self):
        resp = self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertContains(resp, problem.reference_number, count=2, status_code=200)
        self.assertContains(resp, '{0} days after posting'.format(settings.SURVEY_INTERVAL_IN_DAYS))
        self.assertEqual(problem.organisation, self.test_organisation)
        self.assertEqual(problem.service, self.test_service)
        self.assertEqual(problem.public, False)
        self.assertEqual(problem.public_reporter_name, False)
        self.assertEqual(problem.description, 'This is a problem')
        self.assertEqual(problem.reporter_name, self.uuid)
        self.assertEqual(problem.reporter_email, 'steve@mysociety.org')
        self.assertEqual(problem.preferred_contact_method, 'phone')
        self.assertEqual(problem.mailed, False)
        self.assertEqual(problem.confirmation_sent, None)
        self.assertEqual(problem.confirmation_required, True)
        self.assertEqual(problem.survey_sent, None)

    def test_problem_form_respects_name_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PRIVATE_NAME
        self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, False)

    def test_problem_form_sets_name_to_private_for_under_16(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PUBLIC # all public
        self.test_problem['reporter_under_16'] = True
        self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, False)

    def test_problem_form_respects_public_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PUBLIC
        self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, True)

    def test_problem_form_errors_without_email_or_phone(self):
        # test correctly formatted
        self.test_problem['reporter_email'] = 'not an email.com'
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_email', 'Enter a valid e-mail address.')
        # test required
        del self.test_problem['reporter_email']
        del self.test_problem['reporter_phone']
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', None, 'You must provide either a phone number or an email address')

    def test_problem_form_checks_phone_is_valid(self):
        self.test_problem['reporter_phone'] = 'not a number'
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_phone', 'Enter a valid phone number.')

    def test_problem_form_accepts_phone_only(self):
        del self.test_problem['reporter_email']
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertFalse(problem.confirmation_required)
        self.assertIsNotNone(problem)

    def test_problem_form_accepts_email_only(self):
        del self.test_problem['reporter_phone']
        # Set the preferred contact method to email, else the validation will fail
        self.test_problem['preferred_contact_method'] = Problem.CONTACT_EMAIL
        self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)

    def test_problem_form_requires_tandc_agreement(self):
        self.test_problem['agree_to_terms'] = False
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'agree_to_terms', 'You must agree to the terms and conditions to use this service.')

    def test_problem_form_requires_name(self):
        del self.test_problem['reporter_name']
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_name', 'This field is required.')

    def test_problem_can_be_elevated(self):
        self.test_problem['elevate_priority'] = True
        self.test_problem['category'] = 'treatment'
        self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.priority, Problem.PRIORITY_HIGH, 'Problem has wrong priority (should be HIGH)')

    def test_elevated_ignored_if_category_does_not_permit(self):
        self.test_problem['elevate_priority'] = True
        self.test_problem['category'] = 'parking'
        self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.priority, Problem.PRIORITY_NORMAL, 'Problem has wrong priority (should be NORMAL)')

    def test_problem_form_saves_cobrand(self):
        self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.cobrand, 'choices')

    def test_problem_form_fails_if_website_given(self):

        # get the form, check the website field is shown
        resp = self.client.get(self.form_url)
        self.assertContains(resp, '<input type="text" name="website"')

        # post spammy data, check it is not accepted
        spam_problem = self.test_problem.copy()
        spam_problem['website'] = 'http://cheap-drugs.com/'
        resp = self.client.post(self.form_url, spam_problem)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('has been rejected' in resp.content)


class ProblemCreateFormBrowserTests(ProblemCreateFormBase, SeleniumTestCase):

    def is_elevate_priority_hidden(self):
        checkbox = self.driver.find_element_by_id('id_elevate_priority')
        return not checkbox.is_displayed()

    def test_currently_in_care_toggling(self):
        d = self.driver
        d.get(self.full_url(self.form_url))

        # Should be disabled initially
        self.assertTrue(self.is_elevate_priority_hidden())

        # Select a category that it applies to
        d.find_element_by_css_selector('input[name="category"][value="dignity"]').click()
        self.assertFalse(self.is_elevate_priority_hidden())

        # Select a category it does not apply to
        d.find_element_by_css_selector('input[name="category"][value="parking"]').click()
        self.assertTrue(self.is_elevate_priority_hidden())

    def test_under_16_toggling(self):
        d = self.driver
        d.get(self.full_url(self.form_url))

        under_16_input = d.find_element_by_id('id_reporter_under_16')
        keep_private_input = d.find_element_by_id('id_privacy_0')
        publish_with_name_input = d.find_element_by_id('id_privacy_2')

        # get the li using jQuery, because selenium has poor tools for traversing the DOM tree.
        publish_with_name_li = d.execute_script('return $("#id_privacy_2").parents("li").get(0)')

        # Should intially not be selected and publish_with_name visible
        self.assertFalse(under_16_input.is_selected())
        self.assertTrue(keep_private_input.is_selected())
        self.assertTrue(publish_with_name_li.is_displayed())
        publish_with_name_li.click()  # click li because input is hidden
        self.assertFalse(keep_private_input.is_selected())
        self.assertTrue(publish_with_name_input.is_selected())

        # check it, publish_with_name should be hidden
        under_16_input.click()
        self.assertTrue(under_16_input.is_selected())
        self.assertTrue(keep_private_input.is_selected())
        self.assertFalse(publish_with_name_input.is_selected())
        self.assertFalse(publish_with_name_li.is_displayed())

        # uncheck, publish_with_name visible again
        under_16_input.click()
        self.assertFalse(under_16_input.is_selected())
        self.assertTrue(keep_private_input.is_selected())
        self.assertTrue(publish_with_name_li.is_displayed())

    def test_privacy_status_preserved(self):

        d = self.driver
        d.get(self.full_url(self.form_url))

        keep_private_input = d.find_element_by_id('id_privacy_0')
        publish_with_name_input = d.find_element_by_id('id_privacy_2')

        # get the li using jQuery, because selenium has poor tools for traversing the DOM tree.
        publish_with_name_li = d.execute_script('return $("#id_privacy_2").parents("li").get(0)')

        # click the publish with name
        publish_with_name_li.click()  # click li because input is hidden
        self.assertFalse(keep_private_input.is_selected())
        self.assertTrue(publish_with_name_input.is_selected())

        # submit form
        d.find_element_by_css_selector('button[type="submit"]').click()

        # check correct privacy option still selected
        self.assertTrue(d.find_element_by_id('id_privacy_2').is_selected())

    def test_service_preserved(self):

        # convert to string because that is what the JS returns
        test_service_id = str(self.test_service.id)

        d = self.driver
        d.get(self.full_url(self.form_url))
        # import IPython; IPython.embed()

        # check that no value set for service
        self.assertEqual(d.execute_script('return $("#id_service").select2("val")'), "")

        # set a value
        d.execute_script('$("#id_service").select2("val", {0})'.format(test_service_id))
        self.assertEqual(d.execute_script('return $("#id_service").select2("val")'), test_service_id)

        # submit form
        d.find_element_by_css_selector('button[type="submit"]').click()

        # check that correct value still set for service
        self.assertEqual(d.execute_script('return $("#id_service").select2("val")'), test_service_id)


class ProblemCreateFormImageTests(ProblemCreateFormBase, ProblemImageTestBase):
    """ Test uploading of images on the problem form """

    # Backported from Django 1.6 - https://github.com/django/django/commit/d194714c0a707773bd470bffb3d67a60e40bb787
    def assertFormsetError(self, response, formset, form_index, field, errors,
                           msg_prefix=''):
        """
        Asserts that a formset used to render the response has a specific error.

        For field errors, specify the ``form_index`` and the ``field``.
        For non-field errors, specify the ``form_index`` and the ``field`` as
        None.
        For non-form errors, specify ``form_index`` as None and the ``field``
        as None.
        """
        # Add punctuation to msg_prefix
        if msg_prefix:
            msg_prefix += ": "

        # Put context(s) into a list to simplify processing.
        contexts = to_list(response.context)
        if not contexts:
            self.fail(msg_prefix + 'Response did not use any contexts to '
                      'render the response')

        # Put error(s) into a list to simplify processing.
        errors = to_list(errors)

        # Search all contexts for the error.
        found_formset = False
        for i, context in enumerate(contexts):
            if formset not in context:
                continue
            found_formset = True
            for err in errors:
                if field is not None:
                    if field in context[formset].forms[form_index].errors:
                        field_errors = context[formset].forms[form_index].errors[field]
                        self.assertTrue(err in field_errors,
                                msg_prefix + "The field '%s' on formset '%s', "
                                "form %d in context %d does not contain the "
                                "error '%s' (actual errors: %s)" %
                                        (field, formset, form_index, i, err,
                                        repr(field_errors)))
                    elif field in context[formset].forms[form_index].fields:
                        self.fail(msg_prefix + "The field '%s' "
                                  "on formset '%s', form %d in "
                                  "context %d contains no errors" %
                                        (field, formset, form_index, i))
                    else:
                        self.fail(msg_prefix + "The formset '%s', form %d in "
                                 "context %d does not contain the field '%s'" %
                                        (formset, form_index, i, field))
                elif form_index is not None:
                    non_field_errors = context[formset].forms[form_index].non_field_errors()
                    self.assertFalse(len(non_field_errors) == 0,
                                msg_prefix + "The formset '%s', form %d in "
                                "context %d does not contain any non-field "
                                "errors." % (formset, form_index, i))
                    self.assertTrue(err in non_field_errors,
                                    msg_prefix + "The formset '%s', form %d "
                                    "in context %d does not contain the "
                                    "non-field error '%s' "
                                    "(actual errors: %s)" %
                                        (formset, form_index, i, err,
                                         repr(non_field_errors)))
                else:
                    non_form_errors = context[formset].non_form_errors()
                    self.assertFalse(len(non_form_errors) == 0,
                                     msg_prefix + "The formset '%s' in "
                                     "context %d does not contain any "
                                     "non-form errors." % (formset, i))
                    self.assertTrue(err in non_form_errors,
                                    msg_prefix + "The formset '%s' in context "
                                    "%d does not contain the "
                                    "non-form error '%s' (actual errors: %s)" %
                                      (formset, i, err, repr(non_form_errors)))
        if not found_formset:
            self.fail(msg_prefix + "The formset '%s' was not used to render "
                      "the response" % formset)

    @override_settings(MAX_IMAGES_PER_PROBLEM=3)
    def test_can_upload_images(self):
        # Add image related form values
        test_images = {
            'images-TOTAL_FORMS': settings.MAX_IMAGES_PER_PROBLEM,
            'images-MAX_NUM_FORMS': settings.MAX_IMAGES_PER_PROBLEM,
            'images-0-id': '',
            'images-0-image': self.jpg,
            'images-0-problem': '',
            'images-1-id': '',
            'images-1-image': self.gif,
            'images-1-problem': '',
            'images-2-id': '',
            'images-2-image': self.bmp,
            'images-2-problem': ''
        }
        self.test_problem.update(test_images)
        self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.images.all().count(), 3)

    @override_settings(MAX_IMAGES_PER_PROBLEM=2)
    def test_user_told_of_file_count_limit(self):
        resp = self.client.get(self.form_url)
        self.assertContains(resp, 'You can add up to 2 images of your problem.', 1, 200)

    @override_settings(ALLOWED_IMAGE_EXTENSIONS=['.jpg', '.gif', '.bmp'])
    def test_user_told_of_file_type_limit(self):
        resp = self.client.get(self.form_url)
        self.assertContains(resp, 'Allowed image types are: .jpg, .gif, .bmp', 1, 200)

    @override_settings(MAX_IMAGES_PER_PROBLEM=2)
    def test_number_of_image_fields_matches_setting(self):
        resp = self.client.get(self.form_url)
        field_html_template = '<input type="file" name="images-{0}-image" id="id_images-{0}-image" />'
        self.assertContains(resp, field_html_template.format(0))
        self.assertContains(resp, field_html_template.format(1))
        self.assertNotContains(resp, field_html_template.format(2))

    @override_settings(ALLOWED_IMAGE_EXTENSIONS=['.jpg', '.gif', '.bmp'])
    def test_image_types(self):
        # Add image related form values
        test_images = {
            'images-TOTAL_FORMS': settings.MAX_IMAGES_PER_PROBLEM,
            'images-MAX_NUM_FORMS': settings.MAX_IMAGES_PER_PROBLEM,
            'images-0-id': '',
            'images-0-image': self.jpg,
            'images-0-problem': '',
            'images-1-id': '',
            'images-1-image': self.gif,
            'images-1-problem': '',
            'images-2-id': '',
            'images-2-image': self.png,  # This should not be allowed
            'images-2-problem': ''
        }
        self.test_problem.update(test_images)
        resp = self.client.post(self.form_url, self.test_problem)
        expected_error_msg = 'Sorry, that is not an allowed image type. Allowed image types are: .jpg, .gif, .bmp'
        self.assertFormsetError(resp, 'image_forms', 2, 'image', expected_error_msg)


class ProblemSurveyFormTests(TestCase):

    def setUp(self):
        self.test_problem = create_test_problem({})
        self.survey_form_url = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                              'response': 'n',
                                                              'id': int_to_base32(self.test_problem.id),
                                                              'token': self.test_problem.make_token(5555)})
        self.form_values = {'happy_service': 'True'}

    def test_form_happy_path(self):
        resp = self.client.post(self.survey_form_url, self.form_values)
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, False)
        self.assertEqual(self.test_problem.happy_service, True)

    def test_form_records_empty_happy_service(self):
        resp = self.client.post(self.survey_form_url, {'happy_service': ''})
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_service, None)

    def test_form_records_false_happy_service(self):
        resp = self.client.post(self.survey_form_url, {'happy_service': 'False'})
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_service, False)
