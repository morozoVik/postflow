from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re


class User(AbstractUser):
    """Расширенная модель пользователя"""
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Телефон должен быть в формате: '+999999999'. Допускается до 15 цифр."
    )

    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True, verbose_name='Телефон')
    birth_date = models.DateField(verbose_name='Дата рождения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата редактирования')


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Post(models.Model):
    """Модель поста"""
    FORBIDDEN_WORDS = ['ерунда', 'глупость', 'чепуха']

    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Текст')
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name='Изображение')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата редактирования')

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """Валидация модели"""
        if self.author and self.author.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - self.author.birth_date.year - (
                    (today.month, today.day) < (self.author.birth_date.month, self.author.birth_date.day)
            )
            if age < 18:
                raise ValidationError('Автор должен быть старше 18 лет')

        title_lower = self.title.lower()
        for word in self.FORBIDDEN_WORDS:
            if word in title_lower:
                raise ValidationError(f'Заголовок не может содержать слово "{word}"')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Comment(models.Model):
    """Модель комментария"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    content = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата редактирования')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.author.username} к посту {self.post.id}'
