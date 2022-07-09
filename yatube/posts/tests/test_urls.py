from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.allowed_pgs = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.restricted_pgs = {
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(PostsURLTests.not_author)

    def test_page_template(self):
        """Проверка соответствия шаблонов для страниц"""

        for url, template in self.allowed_pgs.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'Использован не тот шаблон для {url}',
                )
        for url, template in self.restricted_pgs.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'Использован не тот шаблон для {url}',
                )

    def test_guest_access_rights(self):
        """Проверка доступности страниц гостю."""
        for url in self.allowed_pgs:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'страница {url} не доступна гостю, а должна.',
                )
        for url in self.restricted_pgs:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.FOUND,
                    f'страница {url} доступна гостю, а не должна.',
                )

    def test_create_post(self):
        """Проверка доступности страницы создания поста."""
        response = self.not_author_client.get('/create/')
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Страница создания поста не доступна '
            'зарегистрированному пользователю.',
        )

    def test_post_edit_page_access(self):
        """Проверка прав доступа к странице редактирования поста."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Страница редактирования поста не доступна автору поста.',
        )
        response = self.not_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            'Страница редактирования поста доступна не только автору.',
        )

    def test_unexisting_page(self):
        """Проверка ошибки и шаблона несуществующей страницы."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND,
            'Обращение к несуществующей странице не вернуло код 404.',
        )

    def test_custom_template_404(self):
        """Проверка кастомного шаблона для страницы 404."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(
            response, 'core/404.html',
            'Не использован кастомный шаблон для страницы 404.',
        )

    def test_guest_redirect_url(self):
        """Проверка адреса переадресовки гостя."""
        for url in self.restricted_pgs:
            with self.subTest(url=url):
                response = self.client.get(url)
                redirect = reverse('users:login') + '?next=' + url
                self.assertRedirects(
                    response, redirect,
                    msg_prefix=f'Не верный редирект гостя со страницы {url}',
                )

    def test_not_author_edit_post(self):
        """Проверка редиректа при попытке не автора отредактировать пост."""
        self.assertRedirects(
            self.not_author_client.get(f'/posts/{self.post.id}/edit/'),
            f'/posts/{self.post.id}/',
        )
