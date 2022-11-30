from http import HTTPStatus

from django.test import TestCase
from test_utils import Url


class TestErrorPages(TestCase):
    def test_404_page(self):
        '''
            Проверка наличия кастомного шаблона на ошибку 404
        '''
        url = Url('unexist_page_ever',
                  default_status=HTTPStatus.NOT_FOUND,
                  default_template='core/404.html')

        response = self.client.get(url.url)

        self.assertEqual(response.status_code, url.guest_status)
