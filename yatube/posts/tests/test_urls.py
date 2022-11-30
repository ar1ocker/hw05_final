from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Post, Group
from test_utils import Url

User = get_user_model()


class PostsUrlTests(TestCase):
    '''
        Проверка template и прав доступа
    '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.empty_user = User.objects.create(username='emptyUser')

        cls.author_user = get_user_model().objects.create(username='testUser')

        cls.group = Group.objects.create(title='group title',
                                         slug='group-slug',
                                         description='group description')
        cls.post = Post.objects.create(text='A' * 30,
                                       author=cls.author_user,
                                       group=cls.group)

        cls.urls_map = [
            Url(reverse('posts:index'),
                default_template='posts/index.html',
                default_status=HTTPStatus.OK),

            Url(reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
                default_template='posts/group_list.html',
                default_status=HTTPStatus.OK,
                help_text='Главная страница группы'),

            Url(reverse('posts:profile', kwargs={'username':
                                                 cls.author_user.username}),
                default_template='posts/profile.html',
                default_status=HTTPStatus.OK,
                help_text='Профиль пользователя, автора 1 поста'),

            Url(reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}),
                default_template='posts/post_detail.html',
                default_status=HTTPStatus.OK,
                help_text='Страница поста'),

            Url(reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                author_template='posts/create_post.html',
                author_status=HTTPStatus.OK,
                authorized_template='posts/post_detail.html',
                authorized_status=HTTPStatus.FOUND,
                help_text='Страница изменения поста, доступная только автору'),

            Url(reverse('posts:post_create'),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                default_template='posts/create_post.html',
                default_status=HTTPStatus.OK,
                help_text='Страница создания поста, '
                          'доступная только авторизованным'),

            Url(reverse('posts:add_comment', kwargs={'post_id': cls.post.pk}),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                default_template='posts/post_detail.html',
                default_status=HTTPStatus.OK,
                help_text='Создание нового комментария'),

            Url(reverse('posts:follow_index'),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                default_template='posts/follow.html',
                default_status=HTTPStatus.OK,
                help_text='Страница избранных авторов'
                          ' доступная только авторизованным'),

            Url(reverse('posts:profile_follow',
                        kwargs={'username': cls.author_user.username}),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                default_template='posts/profile.html',
                default_status=HTTPStatus.FOUND,
                help_text='Активирование подписки на автора'),

            Url(reverse('posts:profile_unfollow',
                        kwargs={'username': cls.author_user.username}),
                guest_template='users/login.html',
                guest_status=HTTPStatus.FOUND,
                default_template='posts/profile.html',
                default_status=HTTPStatus.FOUND,
                help_text='Отключение подписки на автора'),
        ]

    def setUp(self):
        super().setUp()

        self.guest_client = Client()
        self.empty_client = Client()
        self.empty_client.force_login(PostsUrlTests.empty_user)

        self.author_client = Client()
        self.author_client.force_login(PostsUrlTests.author_user)

    def test_urls_guest_user(self):
        '''
        Тестирование status_code и template от не авторизованного юзера
        '''

        for url in PostsUrlTests.urls_map:
            with self.subTest(url=url):
                response = self.guest_client.get(url.url)
                self.assertEqual(response.status_code, url.guest_status)

                response_follow = self.guest_client.get(url.url, follow=True)
                self.assertTemplateUsed(response_follow, url.guest_template)

    def test_urls_empty_authorized_user(self):
        '''
            Тестирование status_code и template от авторизованного юзера
        '''

        for url in PostsUrlTests.urls_map:
            with self.subTest(url=url):
                response = self.empty_client.get(url.url)
                self.assertEqual(response.status_code, url.authorized_status)

                resp_follow = self.empty_client.get(url.url, follow=True)
                self.assertTemplateUsed(resp_follow, url.authorized_template)

    def test_urls_author_authorized_user(self):
        '''
        Тестирование status_code и template от авторизованного юзера
        который является автором
        '''

        for url in PostsUrlTests.urls_map:
            with self.subTest(url=url):
                response = self.author_client.get(url.url)
                self.assertEqual(response.status_code, url.author_status)

                resp_follow = self.author_client.get(url.url, follow=True)
                self.assertTemplateUsed(resp_follow, url.author_template)
