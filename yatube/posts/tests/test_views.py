import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from test_utils import (Form, IndividualField, IndividualObject,
                        IterableWithLen, ObjectsInList, Url)

from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextTest(TestCase):
    '''
        Проверка контекстов
    '''
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = User.objects.create(username='testusername')
        group = Group.objects.create(title='Test group',
                                     slug='test-slug',
                                     description='test description')

        post_fabric = (lambda i: Post(text=f'Post {i}',
                                      author=cls.user,
                                      group=group))

        Post.objects.bulk_create([post_fabric(i) for i in range(12)])

        post = Post.objects.first()
        post.image = SimpleUploadedFile('test.gif', SMALL_GIF, 'image/gif')
        post.save()

        post_context = IndividualObject('post',
                                        text=post.text,
                                        group_id=post.group.pk,
                                        image=post.image)

        cls.urls_list = [
            Url(reverse('posts:index'),
                help_text='Главная страница',
                context=[IterableWithLen('page_obj', context_length=10),
                         ObjectsInList('page_obj',
                                       objects_in=post_context)
                         ]
                ),

            Url(reverse('posts:index') + '?page=2',
                help_text='Главная страница, страница 2',
                context=IterableWithLen('page_obj', context_length=2)),

            Url(reverse('posts:group_list', kwargs={'slug': group.slug}),
                help_text='Страница группы',
                context=[IndividualObject('group',
                                          title=group.title,
                                          slug=group.slug,
                                          description=group.description),
                         IterableWithLen('page_obj', 10),
                         ObjectsInList('page_obj',
                                       objects_in=post_context)
                         ]
                ),

            Url(reverse('posts:profile',
                        kwargs={'username': cls.user.username}),
                help_text='Профиль пользователя',
                context=[IndividualObject('profile_user',
                                          id=cls.user.pk,
                                          username=cls.user.username),
                         IterableWithLen('page_obj', 10),
                         ObjectsInList('page_obj',
                                       objects_in=post_context)
                         ]
                ),

            Url(reverse('posts:post_detail', kwargs={'post_id': post.pk}),
                help_text='Страница отдельного поста',
                context=[post_context,
                         Form('form',
                              text=forms.fields.CharField,
                              help_text='Форма комментариев')
                         ]
                ),

            Url(reverse('posts:post_edit', kwargs={'post_id': post.pk}),
                help_text='Страница изменения поста',
                context=[Form('form',
                              text=forms.fields.CharField,
                              group=forms.fields.ChoiceField,
                              image=forms.fields.ImageField),
                         IndividualField('is_edit', True)
                         ]
                ),

            Url(reverse('posts:post_create'),
                help_text='Страница создания поста',
                context=Form('form',
                             text=forms.fields.CharField,
                             group=forms.fields.ChoiceField,
                             image=forms.fields.ImageField)
                )
        ]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.force_login(ContextTest.user)

    def test_context(self):
        '''Проверка контекстов от авторизованного пользователя'''
        for url in ContextTest.urls_list:
            response = self.client.get(url.url)
            with self.subTest(url=url, response=response):
                for context in url.context:
                    resp_context = response.context.get(context.context_name)
                    self.assertEqual(context, resp_context)


class ViewPostOnPages(TestCase):
    '''
    Тестирование появления или не появляения
    созданного поста на страницах
    '''
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = User.objects.create(username='testuser')

        post_group = Group.objects.create(title='Test group',
                                          slug='test-slug',
                                          description='test description')

        other_group = Group.objects.create(title='Other group',
                                           slug='other-group',
                                           description='other')

        post = Post.objects.create(text='text',
                                   author=cls.user,
                                   group=post_group)

        object_in_paginator = IndividualObject('',
                                               text=post.text,
                                               author_id=post.author.pk,
                                               group_id=post.group.pk)

        paginator_in_context = ObjectsInList('page_obj',
                                             objects_in=object_in_paginator)

        cls.urls_list = [
            Url(reverse('posts:index'),
                help_text='Главная страница',
                context=paginator_in_context),

            Url(reverse('posts:group_list', kwargs={'slug': post_group.slug}),
                help_text='Страница группы с постом',
                context=paginator_in_context),

            Url(reverse('posts:profile',
                        kwargs={'username': cls.user.username}),
                help_text='Страница пользователя с постом',
                context=paginator_in_context),

            Url(reverse('posts:group_list', kwargs={'slug': other_group.slug}),
                help_text='Страница группы, где поста быть не должно',
                context=IterableWithLen('page_obj', 0))
        ]

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.force_login(ViewPostOnPages.user)

    def test_context(self):
        '''Тестирование страниц где появляются посты'''
        for url in ViewPostOnPages.urls_list:
            response = self.client.get(url.url)
            with self.subTest(url=url, response=response):
                for context in url.context:
                    resp_context = response.context.get(context.context_name)
                    self.assertEqual(context, resp_context)


class CommentsTest(TestCase):
    '''
        Тестирование комментариев
    '''
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create(username='testusername')
        cls.post = Post.objects.create(text='test text',
                                       author=cls.user)

        comment = Comment.objects.create(post=cls.post,
                                         author=cls.user,
                                         text='test comment')

        cls.comment_in_context = (IndividualObject('',
                                                   post_id=cls.post.pk,
                                                   author_id=cls.user.pk,
                                                   text=comment.text))

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.force_login(CommentsTest.user)

    def test_comment_in_post_detail(self):
        '''
            Тестирование наличия комментария на странице поста
        '''
        context = [IterableWithLen('comments', Comment.objects.count()),
                   ObjectsInList('comments',
                                 objects_in=CommentsTest.comment_in_context)]

        url = Url(reverse('posts:post_detail',
                          kwargs={'post_id': CommentsTest.post.pk}),
                  help_text='Страница поста с 1-м комментирием',
                  context=context)

        response = self.client.get(url.url)

        with self.subTest(url=url, response=response):
            for context in url.context:
                resp_context = response.context.get(context.context_name)
                self.assertEqual(context, resp_context)


class FollowTest(TestCase):
    '''
        Тестирование главной страницы подписок
    '''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create(username='author_user')
        cls.follower = User.objects.create(username='follower_user')
        cls.empty_user = User.objects.create(username='empty_user')

        post_fabric = (lambda i: Post(text=f'Post {i}',
                                      author=cls.author))

        Post.objects.bulk_create([post_fabric(i) for i in range(12)])

        cls.post = Post.objects.first()

        Follow.objects.create(user=cls.follower, author=cls.author)

    def setUp(self):
        super().setUp()

        self.follower_client = Client()
        self.follower_client.force_login(FollowTest.follower)

        self.empty_client = Client()
        self.empty_client.force_login(FollowTest.empty_user)

    def check_context(self, url_obj, response):
        with self.subTest(url=url_obj, reponse=response):
            for context in url_obj.context:
                self.assertEqual(context,
                                 response.context.get(context.context_name))

    def test_view_follower_author(self):
        '''
            Проверка видимости записей автора у подписчика
        '''
        url = Url(reverse('posts:follow_index'),
                  context=IterableWithLen('page_obj', 10))

        response = self.follower_client.get(url.url)

        self.check_context(url, response)

    def test_view_empty_author(self):
        '''
            Проверка, что пустой пользователь не видит ничего
        '''
        url = Url(reverse('posts:follow_index'),
                  context=IterableWithLen('page_obj', 0))

        response = self.empty_client.get(url.url)

        self.check_context(url, response)


class CacheTest(TestCase):
    '''
        Тестирование кеширования страниц
    '''
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_text = 'test text' * 3
        cls.author = User.objects.create(username='authoruser')

        post_fabric = (lambda i: Post(text=f'{i}',
                                      author=cls.author))

        Post.objects.bulk_create([post_fabric(i) for i in range(12)])

        cls.user_follower = User.objects.create(username='followeruser')
        Follow.objects.create(user=cls.user_follower, author=cls.author)

    def setUp(self):
        super().setUp()
        # Создаем пост перед каждым тестом, ибо он каждый раз удаляется
        self.test_text = 'test text' * 3
        self.test_post = Post.objects.create(text=self.test_text,
                                             author=CacheTest.author)

    def test_index_page_cache(self):
        '''
            Тестирование кеширования на главной странице
        '''
        # Чистим кеш
        cache.clear()
        page_url = reverse('posts:index')
        cache_timeout = 20 + 2

        self.assertIn(self.test_text,
                      self.client.get(page_url).content.decode(),
                      'На странице не найден текст')

        self.assertNotIn(self.test_text,
                         self.client.get(page_url + '?page=3').content
                                                              .decode(),
                         'При кешировании не учитываются get параметры')

        self.test_post.delete()
        time.sleep(cache_timeout)

        self.assertNotIn(self.test_text,
                         self.client.get(page_url).content.decode(),
                         'Таймаут кеширования больше установленного')

    def test_follow_page_cache(self):
        '''
            Тестирование кеширования на странице follow
        '''
        cache.clear()
        page_url = reverse('posts:index')
        cache_timeout = 20 + 2

        self.assertIn(CacheTest.test_text,
                      self.client.get(page_url).content.decode(),
                      'На странице не найден текст')

        self.assertNotIn(CacheTest.test_text,
                         self.client.get(page_url + '?page=3').content
                                                              .decode(),
                         'При кешировании не учитываются get параметры')

        self.test_post.delete()
        time.sleep(cache_timeout)

        self.assertNotIn(self.test_text,
                         self.client.get(page_url).content.decode(),
                         'Таймаут кеширования больше установленного')
