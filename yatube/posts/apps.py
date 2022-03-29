from django.apps import AppConfig
from django.core.paginator import Paginator

from yatube.settings import POSTS_ON_PAGE


class PostsConfig(AppConfig):
    name = 'posts'


def get_paginator(queryset, request):
    paginator = Paginator(queryset, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
