import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.user = User.objects.create(username='test_author')
        cls.group = Group.objects.create(
            slug='first',
            title='Тестовый заголовок',
            description='Замечательная группа'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        # Подсчитаем количество записей
        posts_count = Post.objects.count()
        form_data = {
            'author': self.post.author,
            'text': 'Текстовый тест',
            'group': self.group.pk,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(
            Post.objects.count(),
            posts_count + 1
        )
        # Проверяем, что создалась запись
        post_created = Post.objects.first()
        post_fields = {
            post_created.author: self.user,
            post_created.text: form_data['text'],
            post_created.group: self.group,
        }
        for fields, value in post_fields.items():
            with self.subTest(fields=fields):
                self.assertEqual(fields, value)

    def test_create_image(self):
        """Валидная форма создает запись."""
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
        form_data = {
            'text': 'Текстовый тест',
            'image': uploaded,
        }
        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertIn(uploaded.name, Post.objects.first().image.name)

    def test_comment_appears_in_post(self):
        """Проверка добавления комментария авторизованным пользователем."""
        form = CommentForm(data={'text': 'some comment'})
        self.assertTrue(form.is_valid())
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form.data,
            follow=True
        )
        # Проверяем наличие каментов
        self.assertEqual(self.post.comments.last().text, form.data['text'])
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[self.post.pk])
        )

    def test_comment_create_guest(self):
        """Комментировать посты может только авторизованный пользователь"""
        form = CommentForm(data={'text': 'some comment'})
        # Отправляем POST-запрос
        self.guest_client.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form.data,
            follow=True
        )
        # Проверяем наличие комментария
        self.assertIsNone(self.post.comments.first())

    def test_edit_post(self):
        """Валидная форма редактирует запись."""
        posts_count = Post.objects.count()
        form_data = {'text': 'Текстовый тест изменённый'}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что запись отредактировалась
        post_created = Post.objects.first()
        post_fields = {
            post_created.author: self.user,
            post_created.text: form_data['text'],
        }
        for fields, value in post_fields.items():
            with self.subTest(fields=fields):
                self.assertEqual(fields, value)

    def test_guest_create_redirect(self):
        """Редирект не авторизованного гостя на страницу авторизации"""
        reverse_1 = reverse('users:login')
        reverse_2 = reverse('posts:post_create')
        reverse_sum = f'{reverse_1}?next={reverse_2}'
        self.assertRedirects(
            self.guest_client.post(
                reverse('posts:post_create'),
                follow=True), reverse_sum)
