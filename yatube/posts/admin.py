from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'title', 'slug')
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ('description',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('slug',)
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    # Добавляем интерфейс для поиска по тексту постов
    list_editable = ('group',)
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author', 'post')
    # Добавляем интерфейс для поиска по тексту постов
    list_editable = ('text',)
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date', 'author', 'post',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'user', 'author',)
    # Добавляем интерфейс для поиска по тексту постов
    list_editable = ('author',)
    search_fields = ('user', 'author',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('user', 'author',)
    empty_value_display = '-пусто-'


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
