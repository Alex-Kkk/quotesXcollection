from django.contrib.auth import get_user_model
from django.db import models

MODEL_STR_LEN: int = 15

User = get_user_model()


class Post(models.Model):
    """Модель публикаций."""

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts', verbose_name='Автор',
    )
    group = models.ForeignKey(
        'Group', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='posts', verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.text[:MODEL_STR_LEN]


class Group(models.Model):
    """Модель групп."""

    title = models.CharField(max_length=200, verbose_name='название')
    slug = models.SlugField(unique=True, verbose_name='идентификатор')
    description = models.TextField(verbose_name='описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Модель комментариев к публикациям."""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Публикация',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        max_length=300,
        verbose_name='Текст комментария',
        help_text='Напишите комментарий к публикации',
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата комментария',
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author.username}: {self.text[:MODEL_STR_LEN]}'


class Follow(models.Model):
    user = models.ForeignKey(
        User, related_name='follower',
        on_delete=models.CASCADE, verbose_name='Кто',
    )
    author = models.ForeignKey(
        User, related_name='following',
        on_delete=models.CASCADE, verbose_name='На кого',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique follow',
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class Like(models.Model):
    user = models.ForeignKey(
        User, related_name='liked',
        on_delete=models.CASCADE, verbose_name='Кто поставил',
    )
    post = models.ForeignKey(
        Post, related_name='likes',
        on_delete=models.CASCADE, verbose_name='Лайкнутый пост',
    )