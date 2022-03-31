import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from yatube.settings import POSTS_ON_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_author')
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B'
                     )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            image=uploaded,
            group=Group.objects.create(
                slug='test-slug',
                title='Тестовый заголовок')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:main-view'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}):
                    'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}):
                    'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}):
                    'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}):
                    'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:main-view')).context.get('page_obj')[0]
        fields_test = {
            response.text: self.post.text,
            response.image: self.post.image,
        }
        for field, expect in fields_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expect)

    def test_index_page_contains_correct_context_list(self):
        """Контекст шаблона index содержит cписок постов."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:main-view'))
        context = response.context['page_obj'].object_list
        paginator = Paginator(Post.objects.all(), POSTS_ON_PAGE)
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response_group = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug})).context.get(
                        'group')
        )
        response_page = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.post.group.slug})).context.get(
                        'page_obj')[0]
        )
        fields_test = {
            response_group.title: self.post.group.title,
            response_page.text: self.post.text,
            response_group.slug: self.post.group.slug,
            response_page.image: self.post.image,
        }
        for field, expect in fields_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expect)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response_page = (
            self.authorized_client.
            get(reverse('posts:profile',
                kwargs={'username': self.user.username})).context.get(
                    'page_obj')[0]
        )
        response = (
            self.authorized_client.
            get(reverse('posts:profile',
                kwargs={'username': self.user.username}))
        )
        form_fields = {
            response_page.text: self.post.text,
            response_page.image: self.post.image,
            response.context.get('username'): self.post.author,
            response.context.get('count'): self.post.author.posts.count(),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit_page сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = (self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.pk}))
                    )
        self.assertTrue(response.context['is_edit'])
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = (self.authorized_client.get
                    (reverse('posts:post_create'))
                    )
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.
            get(reverse('posts:post_detail',
                kwargs={'post_id': self.post.id})).context.get('post')
        )
        fields_test = {
            response.text: self.post.text,
            response.image: self.post.image,
        }
        for field, expect in fields_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expect)

    def test_post_exist_on_pages(self):
        """пост существует на главной странице, группы, профиля"""
        templates_page_names = {
            reverse('posts:main-view'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
        }
        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(
                    self.post,
                    response.context.get('page_obj').object_list
                )

    def test_cache(self):
        # создаем запись
        post_cache = Post.objects.create(
            text='Тестовый текст 30',
            author=self.user
        )
        # заполняем кэш
        cache_test = self.authorized_client.get(
            reverse('posts:main-view')).content
        # удаляем запись
        post_cache.delete()
        # проверяем кэш
        post_deleted = self.authorized_client.get(
            reverse('posts:main-view')).content
        self.assertEqual(cache_test, post_deleted)
        # проверяем что кэш очистился
        cache.clear()
        response_non_cached = self.authorized_client.get(
            reverse('posts:main-view')).content
        self.assertNotEqual(cache_test, response_non_cached)


class PostGroupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=Group.objects.create(
                slug='test-slug',
                title='Тестовый заголовок')
        )
        cls.post_2 = Post.objects.create(
            text='Тестовый текст 2',
            author=cls.user,
            group=Group.objects.create(
                slug='test-slug-2',
                title='Тестовый заголовок - 2'
            )
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_not_exist_on_pages(self):
        """пост не существует на странице группы не предназначенной"""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post_2.group.slug})
        )
        self.assertNotIn(
            self.post,
            response.context.get('page_obj').object_list
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username='test_author')
        # Создание 13 постов
        POSTS_COUNT = 13
        cls.post_13 = Post.objects.bulk_create(
            [Post(author=cls.user_1,
             text='Test %s' % i) for i in range(POSTS_COUNT)]
        )
        # Формула расчета числа объектов на последней странице
        cls.POSTS_ON_LAST_PAGE = (
            Paginator(Post.objects.all(), POSTS_ON_PAGE).count
            % POSTS_ON_PAGE
        )

    def setUp(self):
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.authorized_client_1.get(reverse('posts:main-view'))
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.authorized_client_1.get(
            reverse('posts:main-view') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_ON_LAST_PAGE)

    def test_first_profile_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.authorized_client_1.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user_1.username}
            )
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGE)

    def test_second_profile_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.authorized_client_1.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_1.username}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.POSTS_ON_LAST_PAGE)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.author = User.objects.create(username='test_author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=Group.objects.create(
                slug='test-slug',
                title='Тестовый заголовок')
        )
        cls.author_2 = User.objects.create(username='test_author 2')
        cls.post = Post.objects.create(
            text='Тестовый текст 2',
            author=cls.author_2,
            group=Group.objects.create(
                slug='test_slug_2',
                title='Тестовый заголовок 2')
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author_2,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.author)

    def test_create_follow(self):
        """Проверяем подписку"""
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_follow', args=[self.author]),
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.author])
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        fields_test = {
            self.follow.user: self.user,
            self.follow.author: self.post.author,
        }
        for field, expect in fields_test.items():
            with self.subTest(field=field):
                self.assertEqual(field, expect)

    def test_unfollow(self):
        """Проверяем отписку"""
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow', args=[self.author_2]),
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[self.author_2])
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author_2
            ).exists()
        )

    def test_post_on_follow(self):
        """Проверяем запись в лентах у подписчиков"""
        post = Post.objects.create(
            text='Тестовый для подписчика',
            author=self.author_2
        )
        follow_subscriber = self.authorized_client.get(
            reverse('posts:follow_index')).context.get('page_obj').object_list
        self.assertIn(post, follow_subscriber)

    def test_post_on_unfollow(self):
        """Проверяем отсутствие записи в лентах у не подписчиков"""
        post = Post.objects.create(
            text='Тестовый для не подписчика',
            author=self.author_2
        )
        follow_not_subscriber = self.authorized_client_2.get(
            reverse('posts:follow_index')).context.get('page_obj').object_list
        self.assertNotIn(post, follow_not_subscriber)
