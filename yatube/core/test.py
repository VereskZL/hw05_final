from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /not_found/."""
        response = self.guest_client.get('/not_found/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /not_found/."""
        response = self.guest_client.get('/not_found/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_403_error(self):
        response = self.guest_client.get('/admin')
        response.status_code = 403
        self.assertTemplateUsed(response, 'core/403csrf.html')
