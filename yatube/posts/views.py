from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    '''
    Главная страница проекта Yatube
    '''

    posts = Post.objects.select_related('group', 'author').all()

    paginator = Paginator(posts, 10)

    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }

    return render(request, 'posts/index.html', context)


def group_post(request, slug):
    '''
    Отображение всех постов определенной группы
    '''

    group = get_object_or_404(Group, slug=slug)

    posts = (Post.objects.filter(group=group)
                         .select_related('group', 'author')
                         .all())

    paginator = Paginator(posts, 10)

    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    '''
    Отображение информации об определенном пользователе и его постах
    '''

    author = get_object_or_404(User, username=username)

    posts = author.posts.select_related('group').all()

    paginator = Paginator(posts, 10)

    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': author,
        'page_obj': page_obj
    }

    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author).exists():
            context['following'] = True
    # profile_user вместо user, чтобы не переопределять то,
    # что добавляет встроенный в django context_processor auth
    # (в противном случае баги в шапке)

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id, override_comment_form=None):
    '''
        Отображение информации определенного поста
    '''

    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm()
    comments = Comment.objects.filter(post=post.pk).select_related('author')
    context = {
        'post': post,
        'form': override_comment_form or comment_form,
        'comments': comments
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    '''
        Форма для создания постов
    '''

    if request.method == 'POST':
        user = get_object_or_404(User, pk=request.user.pk)
        post = Post(author=user)
        form = PostForm(request.POST,
                        files=request.FILES or None,
                        instance=post)

        if form.is_valid():
            form.save()
            return redirect('posts:profile', request.user.username)
        else:
            return render(request, 'posts/create_post.html', {'form': form})
    else:
        form = PostForm()
        return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    '''
        Форма редактирования постов
    '''
    post = get_object_or_404(Post, pk=post_id)

    # Проверка на право редактирования поста
    if request.user.pk != post.author.pk:
        return redirect('posts:post_detail', post.pk)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    else:
        return render(request,
                      'posts/create_post.html',
                      {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    '''
        Добавление комментария к посту
    '''

    post = get_object_or_404(Post, id=post_id)
    comment = Comment(post=post, author=request.user)
    form = CommentForm(request.POST or None, instance=comment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    else:
        # Тут используем вызов вьюхи потому, что нам нужно как то
        # отображать ошибки формы, если просто редиректить - ошибка не
        # отобразится. На данный момент форма не содержит кучи полей,
        # но кто знает, как оно будет дальше
        return post_detail(request, post_id, override_comment_form=form)


@login_required
def follow_index(request):
    '''
        Главная страница с подписками пользователя
    '''

    user = request.user

    # SELECT * FROM "posts_post" WHERE "posts_post"."author_id"
    # IN (SELECT U0."author_id" FROM "posts_follow" U0 WHERE U0."user_id" = 7)
    # ORDER BY "posts_post"."pub_date" DESC

    # Предложенный вами запрос
    # Post.objects.filter(author__following__user=user)
    # вызывает два JOIN, подскажите, какой запрос будет оптимальней?
    #
    # Код запроса
    # SELECT * FROM "posts_post"
    # INNER JOIN "auth_user"
    # ON ("posts_post"."author_id" = "auth_user"."id")
    # INNER JOIN "posts_follow"
    # ON ("auth_user"."id" = "posts_follow"."author_id")
    # WHERE "posts_follow"."user_id" = 1
    # ORDER BY "posts_post"."pub_date" DESC
    post = (Post.objects
            .filter(author__in=user.follower.values('author'))
            .select_related('group', 'author')
            .all())

    paginator = Paginator(post, 10)

    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    '''
        Подписка пользователя на автора
    '''

    user = request.user
    author = get_object_or_404(User, username=username)
    profile_redirect = redirect('posts:profile', author.username)

    # Не даем подписываться на самих себя
    if user == author:
        return profile_redirect

    # Изначально использовал .exists() из тех соображений,
    # что нам не нужен объект, а значит таскать его из базы нет
    # никакой необходимости
    # Подскажите, насколько Django ORM ленив и не будет ли шорткат
    # get_or_create нагружать канал между базой и Django
    # в реальном приложении при большом потоке запросов?
    Follow.objects.get_or_create(user=user, author=author)

    return profile_redirect


@login_required
def profile_unfollow(request, username):
    '''
        Отписка пользователя от автора
    '''

    user = request.user
    author = get_object_or_404(User, username=username)

    # Подписаться на себя мы не можем, значит и нечего дергать базу лишний раз
    # когда мы знаем что ответ будет пустой
    if user != author:
        Follow.objects.filter(user=user, author=author).delete()

    return redirect('posts:profile', author.username)
