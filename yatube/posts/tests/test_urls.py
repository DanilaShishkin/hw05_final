from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.user = User.objects.create(username='Тестовый автор')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованного пользователя
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создадим и авторизуем пользователя автора поста
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.post.author)
        # Шаблоны по адресам
        self.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        self.urls_auth = {'/create/', '/follow/', }

    def test_unexisting_url_exists_for_guest_users(self):
        """Страница /unexisting/ выдает ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_url_uses_custom(self):
        """Страница /unexisting/ использует кастомный шаблон."""
        response = self.guest_client.get('/unexisting_page/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)

    def test_pages_urls_for_guest_users(self):
        for address in self.templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем страницы доступные авторизованному пользователю
    def test_create_url_exists_at_desired_location(self):
        """Страницы доступны авторизованному пользователю."""
        for address in self.urls_auth:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем страницы доступные автору поста
    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /post_edit/ доступна автору поста."""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_follow_uses_correct_template(self):
        """URL-адрес избранных авторов использует соответствующий шаблон."""
        response = self.authorized_client.get('/follow/')
        template = 'posts/follow.html'
        self.assertTemplateUsed(response, template)

    def test_guest_follow_redirect(self):
        """Редирект гостя со страницы избранных на страницу авторизации"""
        reverse_1 = reverse('users:login')
        reverse_2 = reverse('posts:follow_index')
        reverse_sum = f'{reverse_1}?next={reverse_2}'
        self.assertRedirects(
            self.guest_client.post(
                reverse('posts:follow_index'),
                follow=True), reverse_sum)
