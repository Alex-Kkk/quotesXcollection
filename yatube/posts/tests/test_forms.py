import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):
    """Тестирование форм."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form_test_user = User.objects.create_user(
            username='form_test_user'
        )
        cls.test_form = PostForm()
        cls.test_post = Post.objects.create(
            author=cls.form_test_user,
            text='Текст будет изменен',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FormTests.form_test_user)

    def fields_verify(self, reference, model_instance):
        """Функция для проверки значений инстанса публикации
        по словарю-референсу.
        """
        for field in reference:
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(model_instance, field),
                    reference[field],
                    f'Поле {field} не соответствует эталонному значению.',
                )

    def test_auth_user_creates_post(self):
        """Проверка создания поста в БД после отправки формы
        авторизированным пользователем.
        """
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
        db_count = Post.objects.count()
        form_data = {
            'text': 'Тест форм: тестовый пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={**form_data, **{'image': uploaded}},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.form_test_user,)),
        )
        self.assertEqual(
            Post.objects.count(), db_count + 1,
            'Количество записей в БД не увеличилось.'
        )
        created_post = Post.objects.first()
        reference_data = {
            'text': 'Тест форм: тестовый пост',
            'group': self.group,
            'image': 'posts/' + uploaded.name,
            'author': self.form_test_user,
        }
        self.fields_verify(reference_data, created_post)

    def test_auth_user_modifies_post(self):
        """Проверка изменения поста в БД после изменения его
        авторизированным пользователем.
        """
        reverse_url = reverse(
            'posts:post_edit', args=(self.test_post.id,),
        )
        form_data = {
            'text': 'Тест форм: измененный текст',
        }
        self.authorized_client.post(
            reverse_url, data=form_data, follow=True
        )
        self.assertEqual(
            Post.objects.get(id=self.test_post.id).text,
            form_data['text'],
            'Изменения не были сохранены в БД.'
        )

    def test_unauth_user_creates_comment(self):
        """Тест отказа в создании комментария к публикации
        навторизованному пользователю.
        """
        db_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        url = reverse('posts:add_comment', args=(self.test_post.id,))
        response = self.client.post(url, data=form_data, follow=True,)
        redirect = '/auth/login/?next=' + url
        self.assertRedirects(response, redirect)
        self.assertEqual(
            Comment.objects.count(), db_count,
            'Неавторизованный все таки создал комментарий в БД.'
        )

    def test_auth_user_creates_comment(self):
        """Тест создания комментария к публикации
        авторизированным пользователем.
        """
        db_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.test_post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.test_post.id,)),
        )
        self.assertEqual(
            Post.objects.count(), db_count + 1,
            'Количество комментариев в БД не увеличилось.'
        )
        created_comment = Comment.objects.first()
        reference_data = {
            'text': 'Тестовый коммент',
            'author': self.form_test_user,
        }
        self.fields_verify(reference_data, created_comment)
