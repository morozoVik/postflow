from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Comment, Post, User
from .permissions import IsAdminOrOwner, IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей"""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Настройка прав доступа для разных действий"""
        if self.action == "create":
            # Регистрация доступна всем
            permission_classes = [permissions.AllowAny]
        elif self.action in ["update", "partial_update", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
        elif self.action == "destroy":
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Ограничиваем доступ к списку пользователей"""
        if self.action == "list":
            if self.request.user.is_staff:
                return User.objects.all()
            return User.objects.none()
        return super().get_queryset()


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet для постов"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_permissions(self):
        """Настройка прав доступа для разных действий"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action == "destroy":
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """При создании поста автоматически устанавливаем автора"""
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet для комментариев"""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        """Настройка прав доступа для разных действий"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action == "destroy":
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """При создании комментария автоматически устанавливаем автора"""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Фильтрация комментариев по посту, если передан post_id"""
        queryset = Comment.objects.all()
        post_id = self.request.query_params.get("post_id")

        if post_id:
            queryset = queryset.filter(post_id=post_id)

        return queryset
