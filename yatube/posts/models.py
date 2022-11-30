from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    '''
    Группы в которых могут состоять посты
    '''
    title = models.CharField(max_length=200, verbose_name='Название группы')

    slug = models.SlugField(unique=True, verbose_name='Имя группы для ссылки')
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    '''
    Пользовательские посты
    '''
    text = models.TextField('Текст поста',
                            help_text='Введите текст поста')

    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор')

    group = models.ForeignKey(Group,
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text='Группа,'
                                        ' к которой будет относиться пост')

    image = models.ImageField('Картинка',
                              upload_to='posts/',
                              blank=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments')

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')

    text = models.TextField('Текст')

    created = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE)

    class Meta:
        ordering = ['-author']
