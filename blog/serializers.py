import re
from datetime import date

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import serializers

from .models import Comment, Post, User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя"""

    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "phone",
            "birth_date",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_password(self, value):
        """Валидатор пароля: минимум 8 символов, должен включать цифры"""
        if value:
            if len(value) < 8:
                raise serializers.ValidationError(
                    "Пароль должен содержать минимум 8 символов"
                )

            if not any(char.isdigit() for char in value):
                raise serializers.ValidationError(
                    "Пароль должен содержать хотя бы одну цифру"
                )

            try:
                validate_password(value)
            except ValidationError as e:
                raise serializers.ValidationError(list(e.messages))

        return value

    def validate_email(self, value):
        """Валидатор email: разрешены только домены mail.ru и yandex.ru"""
        if value:
            allowed_domains = ["mail.ru", "yandex.ru"]
            email_domain = value.split("@")[-1].lower()

            if email_domain not in allowed_domains:
                raise serializers.ValidationError(
                    f"Разрешены только email с доменами: {', '.join(allowed_domains)}"
                )

        return value

    def create(self, validated_data):
        """Создание пользователя с хэшированием пароля"""
        password = validated_data.pop("password", None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Обновление пользователя"""
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class PostSerializer(serializers.ModelSerializer):
    """Сериализатор для модели поста"""

    author_username = serializers.CharField(source="author.username", read_only=True)
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    comment_count = serializers.IntegerField(source="comments.count", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "image",
            "author",
            "author_username",
            "author_id",
            "comment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def validate_title(self, value):
        """Валидатор заголовка: запрещенные слова"""
        forbidden_words = ["ерунда", "глупость", "чепуха"]
        title_lower = value.lower()

        for word in forbidden_words:
            if word in title_lower:
                raise serializers.ValidationError(
                    f'Заголовок не может содержать слово "{word}"'
                )

        return value

    def validate(self, data):
        """Валидация возраста автора (только для создания)"""
        request = self.context.get("request")
        if request and hasattr(request, "method") and request.method == "POST":
            author = request.user
            if author.is_authenticated and author.birth_date:

                today = date.today()
                age = (
                    today.year
                    - author.birth_date.year
                    - (
                        (today.month, today.day)
                        < (author.birth_date.month, author.birth_date.day)
                    )
                )
                if age < 18:
                    raise serializers.ValidationError(
                        "Автор должен быть старше 18 лет для создания поста"
                    )

        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели комментария"""

    author_username = serializers.CharField(source="author.username", read_only=True)
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    post_title = serializers.CharField(source="post.title", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_username",
            "author_id",
            "post",
            "post_title",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]
