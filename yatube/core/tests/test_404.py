from django.test import TestCase, Client
from django.test import override_settings


class PageNotFoundTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()

    @override_settings(DEBUG=False)
    def test_404_template(self):
        '''Проверяет правильный вызов шаблона 404'''
        self.assertTemplateUsed(
            self.guest_client.get('random-page/'),
            'core/404.html',
        )
