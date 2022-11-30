from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from test_utils import Url


class TestAboutPages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.about_urls = [
            Url(reverse('about:author'),
                default_template='about/author.html',
                default_status=HTTPStatus.OK,
                help_text='Страница об авторе'),

            Url(reverse('about:tech'),
                default_template='about/tech.html',
                default_status=HTTPStatus.OK,
                help_text='Страница об использованных технологиях')
        ]

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_pages(self):
        """Тестирование всех страниц about"""
        for url in TestAboutPages.about_urls:
            with self.subTest(url=url):
                response = self.client.get(url.url)
                self.assertEqual(response.status_code, url.guest_status)
                self.assertTemplateUsed(response, url.guest_template)
