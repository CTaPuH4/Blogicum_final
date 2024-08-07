from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()
TITLE_MAX_LENGTH = 256
TITLE_SHOWING_LENGTH = 50


class PublishedManager(models.Manager):
    def published(self):
        return self.select_related(
            'category',
            'author',
            'location',
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )


class PublishedModel(models.Model):
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )

    class Meta:
        abstract = True


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True,
        editable=False
    )

    class Meta:
        abstract = True


class Category(PublishedModel, CreatedAtModel):
    title = models.CharField('Заголовок', max_length=TITLE_MAX_LENGTH)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, дефис и подчёркивание.'
                   )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:TITLE_SHOWING_LENGTH]


class Location(PublishedModel, CreatedAtModel):
    name = models.CharField('Название места', max_length=TITLE_MAX_LENGTH)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:TITLE_SHOWING_LENGTH]


class Post(PublishedModel, CreatedAtModel):
    title = models.CharField('Заголовок', max_length=TITLE_MAX_LENGTH)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=('Если установить дату и время '
                   'в будущем — можно делать отложенные публикации.'
                   )

    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )
    objects = models.Manager()
    published_objects = PublishedManager()
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    comment_count = models.PositiveIntegerField(
        'Количество комментариев', default=0
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title[:TITLE_SHOWING_LENGTH]


class Comment(models.Model):
    text = models.TextField('Текст поздравления')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)
