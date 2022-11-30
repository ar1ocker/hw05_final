from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from test_utils import Url

User = get_user_model()


class TestUrlUsers(TestCase):
    """
    Тестируем только signup, т.к. для всего
    остального использован встроенный django.contrib.auth
    и толка его проверять нет
    """

    def test_status_code_and_template_signup(self):
        """Тестирование status_code и template на странице регистрации"""
        client = Client()
        url = Url(reverse('users:signup'),
                  default_template='users/signup.html',
                  default_status=HTTPStatus.OK,
                  help_text='Страница регистрации')

        response = client.get(url.url)
        self.assertEqual(response.status_code, url.guest_status, msg=url)
        self.assertTemplateUsed(response,
                                url.guest_template,
                                msg_prefix=str(url))


class TestViewsUsers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='testuser', password='123')

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.force_login(TestViewsUsers.user)

    def test_templates_in_page_without_csrf_token(self):
        """Проверка всех template которым не нужен csrf_token для входа"""
        urls = [
            Url(reverse('users:logout'),
                default_template='users/logged_out.html'),

            Url(reverse('users:signup'),
                default_template='users/signup.html'),

            Url(reverse('users:login'),
                default_template='users/login.html'),

            Url(reverse('users:password_reset'),
                default_template='users/password_reset_form.html'),

            Url(reverse('users:password_reset_done'),
                default_template='users/password_reset_done.html'),

            Url(reverse('users:password_reset_complete'),
                default_template='users/password_reset_complete.html')
        ]

        for url in urls:
            response = self.client.get(url.url)
            with self.subTest(url=url, response=response):
                self.assertTemplateUsed(response, url.authorized_template)
