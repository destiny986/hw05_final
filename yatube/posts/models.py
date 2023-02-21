from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200, unique=True)
    slug = models.SlugField('Адрес группы', unique=True)
    description = models.TextField('Описание группы')

    class Meta:
        verbose_name = 'группы'
        verbose_name_plural = 'группы'

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )  

    class Meta:
        verbose_name = 'посты'
        verbose_name_plural = 'посты'

    def __str__(self) -> str:
        return self.text[:15]

class Comment(CreatedModel):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Пост к которому относится комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Автор комментария'
    )
    text=models.TextField(
        verbose_name='Текст комментария',
        help_text='Текст комментария'
    )

class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Хелп текст подписчика'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор на кого подписываются',
        help_text='Хелп текст автора на кого подписка'
    )
    
    class Meta:
        unique_together = ('user', 'author',)
