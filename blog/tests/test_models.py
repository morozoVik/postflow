from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from blog.models import Comment, Post

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты для модели пользователя"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user_data = {
            "username": "testuser",
            "email": "test@mail.ru",
            "password": "password123",
            "phone": "+79991234567",
            "birth_date": date(1995, 5, 15),
            "first_name": "Test",
            "last_name": "User",
        }

    def test_create_user(self):
        """Тест создания пользователя"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@mail.ru")
        self.assertEqual(user.phone, "+79991234567")
        self.assertEqual(user.birth_date, date(1995, 5, 15))
        self.assertTrue(user.check_password("password123"))

    def test_user_str_method(self):
        """Тест строкового представления пользователя"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), "testuser")

    def test_user_creation_date_auto_set(self):
        """Тест автоматической установки дат создания и обновления"""
        user = User.objects.create_user(**self.user_data)

        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_user_with_yandex_email(self):
        """Тест создания пользователя с email yandex.ru"""
        self.user_data["email"] = "test@yandex.ru"
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, "test@yandex.ru")

    def test_user_without_phone(self):
        """Тест создания пользователя без телефона"""
        self.user_data["phone"] = ""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.phone, "")


class PostModelTest(TestCase):
    """Тесты для модели поста"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="author",
            email="author@mail.ru",
            password="password123",
            birth_date=date(1990, 1, 1),
        )

        self.post_data = {
            "title": "Test Post",
            "content": "This is test content",
            "author": self.user,
        }

    def test_create_post(self):
        """Тест создания поста"""
        post = Post.objects.create(**self.post_data)

        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.content, "This is test content")
        self.assertEqual(post.author, self.user)
        if hasattr(post, "image") and post.image:
            self.assertIsNone(post.image)
        else:
            self.assertTrue(True)

    def test_post_str_method(self):
        """Тест строкового представления поста"""
        post = Post.objects.create(**self.post_data)
        self.assertEqual(str(post), "Test Post")

    def test_post_ordering(self):
        """Тест сортировки постов по дате создания"""
        post1 = Post.objects.create(**self.post_data)

        post2_data = self.post_data.copy()
        post2_data["title"] = "Second Post"
        post2 = Post.objects.create(**post2_data)

        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)
        self.assertEqual(posts[1], post1)

    def test_post_author_age_validation(self):
        """Тест валидации возраста автора"""
        young_user = User.objects.create_user(
            username="young",
            email="young@mail.ru",
            password="password123",
            birth_date=date(2010, 1, 1),
        )

        post = Post(title="Test Post", content="Content", author=young_user)

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_post_forbidden_words_validation(self):
        """Тест валидации запрещенных слов в заголовке"""
        forbidden_words = ["ерунда", "глупость", "чепуха"]

        for word in forbidden_words:
            post = Post(
                title=f"Это {word} в заголовке", content="Content", author=self.user
            )

            with self.assertRaises(ValidationError):
                post.full_clean()

    def test_post_comment_count(self):
        """Тест подсчета комментариев"""
        post = Post.objects.create(**self.post_data)

        Comment.objects.create(author=self.user, post=post, content="Comment 1")
        Comment.objects.create(author=self.user, post=post, content="Comment 2")

        self.assertEqual(post.comments.count(), 2)


class CommentModelTest(TestCase):
    """Тесты для модели комментария"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter",
            email="commenter@mail.ru",
            password="password123",
            birth_date=date(1990, 1, 1),
        )

        self.post = Post.objects.create(
            title="Test Post", content="Content", author=self.user
        )

        self.comment_data = {
            "author": self.user,
            "post": self.post,
            "content": "This is a test comment",
        }

    def test_create_comment(self):
        """Тест создания комментария"""
        comment = Comment.objects.create(**self.comment_data)

        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.content, "This is a test comment")

    def test_comment_str_method(self):
        """Тест строкового представления комментария"""
        comment = Comment.objects.create(**self.comment_data)
        expected_str = f"Комментарий от {self.user.username} к посту {self.post.id}"
        self.assertEqual(str(comment), expected_str)

    def test_comment_ordering(self):
        """Тест сортировки комментариев по дате создания"""
        comment1 = Comment.objects.create(**self.comment_data)

        comment2_data = self.comment_data.copy()
        comment2_data["content"] = "Second comment"
        comment2 = Comment.objects.create(**comment2_data)

        comments = Comment.objects.all()
        self.assertEqual(comments[0], comment2)
        self.assertEqual(comments[1], comment1)
