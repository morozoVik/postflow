from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from blog.models import Comment, Post
from blog.serializers import CommentSerializer, PostSerializer, UserSerializer

User = get_user_model()


class UserSerializerTest(TestCase):
    """Тесты для сериализатора пользователя"""

    def setUp(self):
        self.valid_data = {
            "username": "testuser",
            "email": "test@mail.ru",
            "password": "password123",
            "phone": "+79991234567",
            "birth_date": "1995-05-15",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_valid_user_serializer(self):
        """Тест валидных данных"""
        test_data = self.valid_data.copy()
        test_data["password"] = "StrongPass123!"
        serializer = UserSerializer(data=test_data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid)

    def test_password_validation_min_length(self):
        """Тест валидации минимальной длины пароля"""
        self.valid_data["password"] = "123"
        serializer = UserSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_validation_requires_digit(self):
        """Тест валидации наличия цифр в пароле"""
        self.valid_data["password"] = "password"
        serializer = UserSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_email_validation_allowed_domains(self):
        """Тест валидации email (разрешенные домены)"""
        test_data = self.valid_data.copy()
        test_data["password"] = "StrongPass123!"

        test_data["email"] = "test@mail.ru"
        serializer = UserSerializer(data=test_data)
        self.assertTrue(
            serializer.is_valid(), f"Email test@mail.ru failed: {serializer.errors}"
        )

        test_data["email"] = "test@yandex.ru"
        serializer = UserSerializer(data=test_data)
        self.assertTrue(
            serializer.is_valid(), f"Email test@yandex.ru failed: {serializer.errors}"
        )

        test_data["email"] = "test@gmail.com"
        serializer = UserSerializer(data=test_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_create_user_with_password_hashing(self):
        """Тест создания пользователя с хэшированием пароля"""
        test_data = self.valid_data.copy()
        test_data["password"] = "StrongPass123!"
        test_data["phone"] = "+79991112233"
        serializer = UserSerializer(data=test_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertNotEqual(user.password, "StrongPass123!")

    def test_update_user(self):
        """Тест обновления пользователя"""
        user = User.objects.create_user(
            username="olduser",
            email="old@mail.ru",
            password="oldpass123",
            birth_date=date(1995, 5, 15),
        )

        update_data = {"username": "newusername", "email": "new@mail.ru"}

        serializer = UserSerializer(instance=user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.username, "newusername")
        self.assertEqual(updated_user.email, "new@mail.ru")
        self.assertTrue(updated_user.check_password("oldpass123"))


class PostSerializerTest(TestCase):
    """Тесты для сериализатора поста"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="author",
            email="author@mail.ru",
            password="password123",
            birth_date=date(1990, 1, 1),
        )

        self.valid_data = {
            "title": "Test Post",
            "content": "This is test content",
            "image": None,
        }

        class MockRequest:
            user = self.user
            method = "POST"

        self.context = {"request": MockRequest()}

    def test_valid_post_serializer(self):
        """Тест валидных данных"""
        serializer = PostSerializer(data=self.valid_data, context={"request": self})
        self.assertTrue(serializer.is_valid())

    def test_title_forbidden_words_validation(self):
        """Тест валидации запрещенных слов в заголовке"""
        forbidden_words = ["ерунда", "глупость", "чепуха"]

        for word in forbidden_words:
            self.valid_data["title"] = f"Это {word} в заголовке"
            serializer = PostSerializer(data=self.valid_data, context=self.context)
            self.assertFalse(serializer.is_valid())
            self.assertIn("title", serializer.errors)

    def test_author_age_validation(self):
        """Тест валидации возраста автора"""
        young_user = User.objects.create_user(
            username="young",
            email="young@mail.ru",
            password="password123",
            birth_date=date(2010, 1, 1),
        )

        class YoungUserRequest:
            user = young_user
            method = "POST"

        context = {"request": YoungUserRequest()}

        serializer = PostSerializer(data=self.valid_data, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_post_serializer_read_only_fields(self):
        """Тест полей только для чтения"""
        serializer = PostSerializer()
        self.assertIn("id", serializer.Meta.read_only_fields)
        self.assertIn("created_at", serializer.Meta.read_only_fields)
        self.assertIn("updated_at", serializer.Meta.read_only_fields)
