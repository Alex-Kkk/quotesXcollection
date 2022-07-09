from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import MODEL_STR_LEN, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестирование моделей."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_model_str(self):
        """Проверяем, что у модели постов корректно работает __str__."""
        self.group_string = str(PostModelTest.group)
        self.group_expected = PostModelTest.group.title
        self.assertEqual(
            self.group_string, self.group_expected,
            'Некорректно работает метод __str__ модели Group'
        )

    def test_group_model_str(self):
        """Проверяем, что у модели групп корректно работает __str__."""
        self.post_string = str(PostModelTest.post)
        self.post_expected = PostModelTest.post.text[:MODEL_STR_LEN]
        self.assertEqual(
            self.post_string, self.post_expected,
            'Некорректно работает метод __str__ модели Post'
        )

    def test_verbose_names(self):
        """verbose_name в полях модели совпадает с ожидаемым."""
        self.model = PostModelTest.post
        self.field_verboses = {
            'text': 'Текст поста',
            'author': 'Автор',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_name in self.field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.model._meta.get_field(field).verbose_name,
                    expected_name,
                    f'Неверный либо отсутствует verbose_name поля {field}',
                )

    def test_help_text(self):
        """help_text в полях модели совпадает с ожидаемым."""
        self.model = PostModelTest.post
        self.field_help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_text in self.field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.model._meta.get_field(field).help_text,
                    expected_text,
                    f'Неверный либо отсутствует help_text поля {field}'
                )
