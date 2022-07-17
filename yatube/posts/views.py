from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.http import HttpResponse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, Like
from posts.utils import paginate


POSTS_MAX: int = 10

User = get_user_model()


def index(request):
    """Главная страница. Все публикации."""
    post_list = Post.objects.select_related('author', 'group')
    page_obj = paginate(request, post_list, POSTS_MAX)
    context = {'page_obj': page_obj}

    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    """Страница группы. Публикации выбранной группы."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group')
    page_obj = paginate(request, post_list, POSTS_MAX)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница профиля пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author', 'group')
    page_obj = paginate(request, post_list, POSTS_MAX)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница отдельной взятой публикации."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id,
    )
    comments = post.comments.select_related('author')
    form = CommentForm()
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post_id).exists()
    else:
        liked = False

    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'liked': liked,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница создания новой публикации."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            return redirect('posts:profile', request.user.username)

    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования публикации."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id,
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.method == 'POST' and form.is_valid:
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:post_detail', post_id)

    return render(
        request, 'posts/post_create.html',
        {'form': form, 'is_edit': True, 'post_id': post_id},
    )


@login_required
def add_comment(request, post_id):
    """Представление для добавления комментария к публикации."""
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Представление с публикациями любимых авторов."""
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = paginate(request, post_list, POSTS_MAX)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Представление для подписки на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Представление для отписки от автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:profile', username=username)


@login_required
def user_account(request, username):
    """Страница профиля пользователя."""
    user_pr = get_object_or_404(User, username=username)
    context = {
        'user_pr': user_pr,
    }

    return render(request, 'posts/user_account.html', context)


class LikeView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if Like.objects.filter(user=request.user, post=post).exists():
            Like.objects.filter(user=request.user, post=post).delete()
        else:
            Like(user=request.user, post=post).save()

        return HttpResponse()
