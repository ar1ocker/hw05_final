import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from test_utils import Url

from ..models import Comment, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostForms(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()

        self.client = Client()
        self.client.force_login(TestPostForms.user)

    def test_create_post(self):
        """
            Проверка создания поста от авторизованного пользователя
        """
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        url = Url(reverse('posts:post_create'),
                  post_data={'text': 'test text',
                             'image': uploaded},
                  help_text='Страница создания поста с картинкой')

        response = self.client.post(url.url,
                                    data=url.post_data)

        # subtest используется для того, чтобы при ошибке в тесте вывести
        # больше технической информации
        with self.subTest(url=url, response=response):
            self.assertTrue(
                Post.objects.filter(
                    author=TestPostForms.user,
                    text='test text',
                    image='posts/test.gif'
                ).exists()
            )

    def test_edit_post(self):
        """
            Проверка изменения поста
        """
        post = Post.objects.create(text='test text 2',
                                   author=TestPostForms.user)

        uploaded = SimpleUploadedFile(
            name='test2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        url = Url(reverse('posts:post_edit',
                          kwargs={'post_id': post.pk}),
                  post_data={'text': 'new text',
                             'image': uploaded},
                  help_text=f'Страница изменения поста {post.pk}')

        self.client.post(url.url,
                         data=url.post_data)

        post.refresh_from_db()
        self.assertEqual(post.text, 'new text',
                         msg='Не изменился текст')
        self.assertEqual(post.image, 'posts/test2.gif',
                         msg='Не изменилось изображение')


class CommentTest(TestCase):
    """
        Проверка создания комментария
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create(username='testcommentusername')
        cls.post = Post.objects.create(author=cls.user, text='test text')

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(CommentTest.user)

    def test_create_comment_by_form(self):
        """
            Создание комменатрия через add_comment
        """
        add_comment_url = Url(reverse('posts:add_comment',
                                      kwargs={'post_id': CommentTest.post.pk}),
                              post_data={'text': 'comment text'})

        count_comments = Comment.objects.count()

        resp = self.client.post(add_comment_url.url, add_comment_url.post_data)

        self.assertEqual(count_comments + 1, Comment.objects.count(), msg=resp)
