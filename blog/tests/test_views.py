from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from blog.models import Comment, Post

User = get_user_model()


class UserViewSetTest(TestCase):
    """Тесты для эндпоинтов пользователей"""

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@mail.ru",
            password="adminpass123",
            birth_date=date(1980, 1, 1),
        )

        self.regular_user = User.objects.create_user(
            username="user",
            email="user@mail.ru",
            password="userpass123",
            birth_date=date(1995, 5, 15),
        )

        self.user_data = {
            "username": "newuser",
            "email": "new@mail.ru",
            "password": "newpass123",
            "birth_date": "2000-01-01",
            "phone": "+79998887766",
        }

    def test_user_registration(self):
        """Тест регистрации нового пользователя"""
        response = self.client.post(reverse("user-list"), self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(response.data["username"], "newuser")

    def test_user_registration_invalid_email(self):
        """Тест регистрации с невалидным email"""
        self.user_data["email"] = "user@gmail.com"
        response = self.client.post(reverse("user-list"), self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_registration_invalid_password(self):
        """Тест регистрации с невалидным паролем"""
        self.user_data["password"] = "123"
        response = self.client.post(reverse("user-list"), self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_list_admin_only(self):
        """Тест: только админ может видеть список пользователей"""
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_user_update_own_profile(self):
        """Тест: пользователь может обновлять свой профиль"""
        self.client.force_authenticate(user=self.regular_user)

        update_data = {"first_name": "Updated", "last_name": "Name"}

        response = self.client.patch(
            reverse("user-detail", args=[self.regular_user.id]), update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, "Updated")
        self.assertEqual(self.regular_user.last_name, "Name")

    def test_user_cannot_update_other_profile(self):
        """Тест: пользователь не может обновлять чужой профиль"""
        self.client.force_authenticate(user=self.regular_user)

        update_data = {"first_name": "Hacked"}

        response = self.client.patch(
            reverse("user-detail", args=[self.admin_user.id]), update_data
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_admin_only(self):
        """Тест: только админ может удалять пользователей"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(
            reverse("user-detail", args=[self.regular_user.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(
            reverse("user-detail", args=[self.regular_user.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class PostViewSetTest(TestCase):
    """Тесты для эндпоинтов постов"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="author",
            email="author@mail.ru",
            password="pass123",
            birth_date=date(1990, 1, 1),
        )

        self.other_user = User.objects.create_user(
            username="other",
            email="other@mail.ru",
            password="pass123",
            birth_date=date(1992, 2, 2),
        )

        self.post_data = {"title": "Test Post", "content": "This is test content"}

        self.post = Post.objects.create(
            title="Existing Post", content="Content", author=self.user
        )

    def test_create_post_authenticated(self):
        """Тест: авторизованный пользователь может создать пост"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("post-list"), self.post_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Post")
        self.assertEqual(response.data["author"], self.user.id)

    def test_create_post_unauthenticated(self):
        """Тест: неавторизованный пользователь не может создать пост"""
        response = self.client.post(reverse("post-list"), self.post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_posts_all_users(self):
        """Тест: все пользователи могут видеть список постов"""
        response = self.client.get(reverse("post-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("post-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_own_post(self):
        """Тест: автор может обновить свой пост"""
        self.client.force_authenticate(user=self.user)

        update_data = {"title": "Updated Title"}
        response = self.client.patch(
            reverse("post-detail", args=[self.post.id]), update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Title")

    def test_cannot_update_other_post(self):
        """Тест: нельзя обновить чужой пост"""
        self.client.force_authenticate(user=self.other_user)

        update_data = {"title": "Hacked Title"}
        response = self.client.patch(
            reverse("post-detail", args=[self.post.id]), update_data
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_post(self):
        """Тест: автор может удалить свой пост"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse("post-detail", args=[self.post.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_forbidden_words_validation(self):
        """Тест: валидация запрещенных слов в заголовке"""
        self.client.force_authenticate(user=self.user)

        self.post_data["title"] = "Это полная ерунда"
        response = self.client.post(reverse("post-list"), self.post_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)


class CommentViewSetTest(TestCase):
    """Тесты для эндпоинтов комментариев"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="commenter",
            email="commenter@mail.ru",
            password="pass123",
            birth_date=date(1990, 1, 1),
        )

        self.post = Post.objects.create(
            title="Test Post", content="Content", author=self.user
        )

        self.comment_data = {"post": self.post.id, "content": "Great post!"}

        self.comment = Comment.objects.create(
            author=self.user, post=self.post, content="Existing comment"
        )

    def test_create_comment_authenticated(self):
        """Тест: авторизованный пользователь может создать комментарий"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("comment-list"), self.comment_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Great post!")
        self.assertEqual(response.data["author"], self.user.id)

    def test_create_comment_unauthenticated(self):
        """Тест: неавторизованный пользователь не может создать комментарий"""
        response = self.client.post(reverse("comment-list"), self.comment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_comments_all_users(self):
        """Тест: все пользователи могут видеть комментарии"""
        response = self.client.get(reverse("comment-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_comments_by_post(self):
        """Тест: фильтрация комментариев по посту"""
        response = self.client.get(reverse("comment-list"), {"post_id": self.post.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_update_own_comment(self):
        """Тест: автор может обновить свой комментарий"""
        self.client.force_authenticate(user=self.user)

        update_data = {"content": "Updated comment"}
        response = self.client.patch(
            reverse("comment-detail", args=[self.comment.id]), update_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment")

    def test_delete_own_comment(self):
        """Тест: автор может удалить свой комментарий"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse("comment-detail", args=[self.comment.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)
