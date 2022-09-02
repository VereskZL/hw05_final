import shutil

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm
from ..models import Post, Group
from .test_views import SMALL_GIF, TEMP_MEDIA_ROOT

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VIP_NPS')
        cls.uploaded_file = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_file
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'imade': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit(self):
        """При редактировании поста изменяется запись в базе данных."""
        text_after_edit = 'Тестовый пост после редактирования'
        form_data = {
            'text': text_after_edit,
            'group': self.group.id,
            'imade': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post_after_edit = response.context['post']
        self.assertEqual(post_after_edit.text, form_data.get('text'))
        self.assertEqual(post_after_edit.group.id, form_data.get('group'))


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VIP_NPS')
        cls.user = User.objects.create_user(username='MarieL')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.guest_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()
        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={
                'post_id': cls.post.id}
        )
