from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory

from .views import bb_upload
# Create your tests here.

from .utils.sample_data_bb import SAMPLE_BB_TEXT


class PostBlueButtonFileTest(TestCase):
    """ Test the BlueButton Upload """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='jacob', email='jacob@…', password='top_secret')

    def test_not_logged_in_fail(self):
        """ BBUpload - User not logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = AnonymousUser()

        format = "html"
        payload = {"bb_text": SAMPLE_BB_TEXT,
                   "output_format": format}
        result = bb_upload(request, payload)

        print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         302)

    def test_user_logged_in_success(self):
        """ BBUpload - User Logged in """

        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user

        format = "html"
        payload = {"bb_text": SAMPLE_BB_TEXT,
                   "output_format": format}
        result = bb_upload(request, payload)

        print("Result:%s" % result)

        self.assertEqual(result.status_code,
                         200)
