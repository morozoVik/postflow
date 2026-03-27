from django.contrib import admin
from django.utils.html import format_html
from .models import User, Post, Comment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'birth_date', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone', 'birth_date')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_link', 'created_at', 'updated_at', 'comment_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('author',)

    def author_link(self, obj):
        """Ссылка на автора в админке"""
        return format_html('<a href="/admin/blog/user/{}/">{}</a>', obj.author.id, obj.author.username)

    author_link.short_description = 'Автор'
    author_link.admin_order_field = 'author'

    def comment_count(self, obj):
        """Количество комментариев к посту"""
        return obj.comments.count()

    comment_count.short_description = 'Комментариев'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at', 'short_content')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('author', 'post')

    def short_content(self, obj):
        """Сокращенный текст комментария"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Текст'
