import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from posts.views import POSTS_MAX

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

TEST_POSTS_QTY = int(POSTS_MAX * 1.5)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    """Тестирование представлений."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='test_user')
        cls.other_user = User.objects.create_user(username='other_user')
        cls.subscribed_user = User.objects.create_user(
            username='subscribed_user',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Другая группа',
            slug='other-slug',
            description='Другое описание',
        )
        Post.objects.bulk_create(
            cls.generate_posts(cls, TEST_POSTS_QTY),
        )
        cls.post = Post.objects.first()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)
        self.other_client = Client()
        self.other_client.force_login(self.other_user)
        self.subscribed_client = Client()
        self.subscribed_client.force_login(self.subscribed_user)

    def generate_posts(self, quantity):
        """Генератор для создания нескольких постов в тестовой БД."""
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=test_image,
            content_type='image/gif'
        )
        return [
            Post(
                author=self.test_user,
                text=f'Тест пост # {i + 1}',
                group=self.group,
                image=uploaded,
            ) for i in range(quantity)
        ]

    def form_fields_verify(self, form_fields, view, *args):
        """Функция для проверки полей форм."""
        response = self.authorized_client.get(
            reverse(view, args=args)
        )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(
                    form_field, expected,
                    f'Поле формы {value} не соответствует типу {expected}.'
                )

    def compare_obj_content(self, obj_from_db, obj_from_page):
        """Функция для сравнения значений полей двух объектов модели."""
        model = type(obj_from_db)
        fields = model._meta.fields
        for field in fields:
            self.assertEqual(
                getattr(obj_from_db, field.name),
                getattr(obj_from_page, field.name),
                f'Не соответствует {field.name} модели {model.__name__}',
            )

    def test_templates(self):
        """Проверка шаблонов отображений."""
        pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=(self.group.slug,)):
                'posts/group_list.html',
            reverse('posts:profile', args=(self.test_user,)):
                'posts/profile.html',
            reverse('posts:post_detail', args=(self.post.id,)):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', args=(self.post.id,)):
                'posts/post_create.html',
        }
        for reverse_name, template in pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(
                    response, template,
                    f'Использован неверный шаблон в {reverse_name}',
                )

    def test_index_context(self):
        """Проверка контекста: index"""
        response = self.authorized_client.get(reverse('posts:index'))
        from_db = Post.objects.all()[POSTS_MAX - 1]
        from_page = response.context['page_obj'][POSTS_MAX - 1]
        self.compare_obj_content(from_db, from_page)

    def test_group_list_context(self):
        """Проверка контекста: group_list."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        post_from_db = Post.objects.filter(group=self.group)[POSTS_MAX - 1]
        post_from_page = response.context['page_obj'][POSTS_MAX - 1]
        self.compare_obj_content(post_from_db, post_from_page)
        group_from_db = post_from_db.group
        group_from_page = response.context['group']
        self.compare_obj_content(group_from_db, group_from_page)

    def test_profile_context(self):
        """Проверка контекста: profile."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=('test_user',))
        )
        post_from_db = self.test_user.posts.all()[POSTS_MAX - 1]
        post_from_page = response.context['page_obj'][POSTS_MAX - 1]
        self.compare_obj_content(post_from_db, post_from_page)
        author_from_db = post_from_db.author
        author_from_page = response.context['author']
        self.compare_obj_content(author_from_db, author_from_page)

    def test_post_detail_context(self):
        """Проверка контекста: post_detail."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        from_db = Post.objects.get(pk=self.post.id)
        from_page = response.context['post']
        self.compare_obj_content(from_db, from_page)

    def test_post_create_context(self):
        """Проверка контекста формы: post_create."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.form_fields_verify(form_fields, 'posts:post_create')

    def test_post_edit_context(self):
        """Проверка контекста формы и передаваемого в нее поста."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.form_fields_verify(
            form_fields, 'posts:post_edit', *(self.post.id,),
        )
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(self.post.id,))
        )
        post = Post.objects.get(pk=self.post.id)
        self.assertEqual(
            response.context['form']['text'].value(),
            post.text,
            'В контекст не передается информация о требуемом посте.',
        )
        self.assertTrue(
            response.context['is_edit'],
            'В контекст не передана переменная is_edit.',
        )
        self.assertIsInstance(
            response.context['is_edit'],
            bool,
            'В контексте переменная is_edit не соответствует типу bool.'
        )

    def test_pagination(self):
        """Проверка паджинации первой и второй страницы."""
        test_views = {
            reverse('posts:index'):
                Post.objects.all(),
            reverse('posts:group_list', args=(self.group.slug,)):
                Post.objects.filter(group=self.group),
            reverse('posts:profile', args=(self.test_user,)):
                Post.objects.filter(author=self.test_user),
        }
        for view, queryset in test_views.items():
            with self.subTest(view=view):
                response = self.authorized_client.get(view)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_MAX,
                    'Количество постов на первой странице некорректно '
                    f'на странице {view}',
                )
                response = self.authorized_client.get(view + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    TEST_POSTS_QTY - POSTS_MAX,
                    'Количество постов на второй странице некорректно '
                    f'на странице {view}?page=2',
                )

    def test_new_post_availability(self):
        """Проверка отображения на разных страницах созданного поста."""
        new_post = Post.objects.create(
            author=self.test_user,
            text='Созданный пост',
            group=self.other_group,
        )
        test_views = (
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.other_group.slug,)),
            reverse('posts:profile', args=(self.test_user.username,)),
        )
        for view in test_views:
            with self.subTest(view=view):
                response = self.client.get(view)
                self.assertIn(
                    new_post, response.context['page_obj'],
                    f'Созданный пост отсутствует в {view}',
                )

    def test_posts_appears_in_correct_group(self):
        """Проверка что посты не отображаются не в своих группах."""
        new_post = Post.objects.create(
            author=self.test_user,
            text='Созданный пост',
            group=self.other_group,
        )
        other_group_view = reverse('posts:group_list', args=(self.group.slug,))
        response = self.client.get(other_group_view)
        self.assertNotIn(
            new_post,
            response.context['page_obj'],
            'Созданный пост попал на страницу другой '
            f'группы {other_group_view}',
        )

    def test_post_image(self):
        """Проверка наличия картинок в постах."""
        pages = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=(self.group.slug,)): 'page_obj',
            reverse('posts:profile', args=('test_user',)): 'page_obj',
            reverse('posts:post_detail', args=(self.post.id,)): 'post',
        }
        for view, cntx_name in pages.items():
            response = self.client.get(view)
            if cntx_name == 'post':
                post = response.context[cntx_name]
            else:
                post = response.context[cntx_name][0]
            self.assertIsNotNone(
                post.image,
                f'В представление {view} не передаются картинки постов',
            )

    def test_index_cache(self):
        """Проверка кэшированя главной страницы."""
        post = Post.objects.create(author=self.test_user, text='Тест Кэша')
        self.client.get(reverse('posts:index'))
        post.delete()
        response_second = self.client.get(reverse('posts:index'))
        self.assertIn(
            post.text.encode(),
            response_second.content,
            'Удаленная запись не отобразилась на кешированной странице.'
        )
        cache.clear()
        response_third = self.client.get(reverse('posts:index'))
        self.assertNotIn(
            post.text.encode(),
            response_third.content,
            'Удаленная запись отобразилась на странице после очистки кэша.'
        )

    def test_author_following(self):
        """Проверка возможности подписки на автора."""
        follows = Follow.objects.filter(user=self.test_user)
        db_count = follows.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.other_user.username,))
        )
        db_count_follow = follows.count()
        self.assertEqual(
            db_count + 1, db_count_follow,
            'Авторизованный пользователь не смог подписаться на автора.'
        )

    def test_author_unfollowing(self):
        """Проверка возможности отписки от автора."""
        Follow.objects.create(
            user=self.test_user,
            author=self.other_user,
        )
        follows = Follow.objects.filter(user=self.test_user)
        db_count = follows.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.other_user.username,))
        )
        db_count_unfollow = follows.count()
        self.assertEqual(
            db_count - 1, db_count_unfollow,
            'Авторизованный пользователь не смог отписаться от автора.'
        )

    def test_subscribed_post_display(self):
        """Проверка отображения публикаций на которые
        подписан пользователь.
        """
        follow = Follow.objects.create(
            user=self.subscribed_user,
            author=self.test_user,
        )
        response = self.subscribed_client.get(reverse('posts:follow_index'))
        view_count = response.context['page_obj'].paginator.count
        db_count = follow.author.posts.count()
        self.assertEqual(
            view_count, db_count,
            'Не отображаются, либо не в том количестве публикации любимых '
            'авторов на странице follow_index.'
        )

    def test_unsubscribed_post_display(self):
        """Проверка того что на страницу подписок пользователя не
        попадают лишние публикации"""
        response = self.other_client.get(reverse('posts:follow_index'))
        view_count = response.context['page_obj'].paginator.count
        db_count = Post.objects.filter(
            author__following__user=self.other_user
        ).count()
        self.assertEqual(
            view_count, db_count,
            'На странице не подписанного пользователя есть публикации.'
        )

    def test_auth_user_comment(self):
        """Проверка того что авторизованный пользователь
        может оставлять комментарии."""
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': 'Тестовый комментарий'},
            follow=True,
        )
        self.compare_obj_content(
            response.context['comments'].first(),
            Comment.objects.filter(author=self.test_user).first(),
        )

    def test_guest_user_comment(self):
        """Проверка того что гость не может оставлять комментарии."""
        db_count = Comment.objects.count()
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': 'Я гость'},
            follow=True,
        )
        redirect = (
            reverse('users:login')
            + '?next='
            + reverse('posts:add_comment', args=(self.post.id,))
        )
        self.assertRedirects(response, redirect)
        db_count_after = Comment.objects.count()
        self.assertEqual(
            db_count, db_count_after,
            'Гостю удалось откомментировать публикацию.',
        )
