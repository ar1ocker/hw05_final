from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        author = User.objects.create()
        cls.post = Post.objects.create(text='A' * 30, author=author)

    def test_correct_post_text(self):
        '''Проверка корректности __str__'''
        self.assertEqual(
            str(PostModelTest.post),
            'A' * 15,
            '__str__ не ограничивает вывод в 15 символов')


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(title='A' * 30)

    def test_correct_group_title(self):
        '''Проверка корректности __str__'''
        self.assertEqual(
            str(GroupModelTest.group),
            'A' * 30,
            '__str__ Не выводит название группы')
