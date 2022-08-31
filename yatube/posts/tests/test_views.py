import shutil
import tempfile

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from django import forms

from ..models import Group, Post, Follow, Comment

User = get_user_model()

INDEX = reverse('posts:main_posts')
FOLLOW_INDEX = reverse('posts:follow_index')
CREATE = reverse('posts:create_post')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

COMMENT_TEXT = 'Test comment'

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.some_user = User.objects.create_user(username='NPS')
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
        cls.POST_DETAL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT = reverse(
            'posts:edit', kwargs={'post_id': cls.post.id}
        )
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.post.author})
        cls.GROUP = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.some_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            INDEX: 'posts/index.html',
            self.GROUP: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_DETAL: 'posts/post_detail.html',
            CREATE: 'posts/create_post.html',
            self.POST_EDIT: 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls = [
            INDEX,
            self.GROUP,
            self.PROFILE,
        ]
        for url in urls:
            response = self.authorized_client.get(url)
            first_post = response.context['page_obj'][0]
            self.assertPostsEqual(first_post, self.post)

    def assertPostsEqual(self, post1, post2):
        self.assertEqual(post1.text, post2.text)
        self.assertEqual(post1.group, post2.group)
        self.assertEqual(post1.author, post2.author)
        self.assertEqual(post1.image, post2.image)

    def test_group_list_correct_context(self):
        """Шаблоы сформированы с правильным контекстом."""
        response = self.authorized_client.get(self.GROUP)
        group = response.context['group']
        expected_group = self.group
        self.assertEqual(group, expected_group)

    def test_edit_page_show_correct_context(self):
        response = self.authorized_client.get(self.POST_DETAL)
        first_post = response.context['post']
        self.assertEqual(first_post, self.post)

    def test_create_and_edit_correct_context(self):
        urls = [
            CREATE,
            self.POST_EDIT
        ]
        for url in urls:
            response = self.authorized_client.get(url)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VIP_NPS')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',)
        for index in range(13):
            note = f"запись номер {index} "
            Post.objects.create(
                text=note,
                author=cls.user,
                group=cls.group
            )
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.user})
        cls.GROUP = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug})

    def test_first_page_contains_ten_records(self):
        urls = [
            INDEX,
            self.PROFILE,
            self.GROUP

        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)
            response = self.client.get(url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)


class NewPostTests(TestCase):
    """Проверяем, что пост создается там, где нужно"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VIP_NPS')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.uploaded_file = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.anower_group = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded_file
        )
        cls.PROFILE = reverse(
            'posts:profile', kwargs={'username': cls.post.author})
        cls.GROUP = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug})
        cls.ANOWER_GROUP = reverse(
            'posts:group_list', kwargs={'slug': cls.anower_group.slug})

    def test_new_post(self):
        urls = [
            INDEX,
            self.PROFILE,
            self.GROUP,
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 1)

    def test_no_new_post_on_anower_group(self):
        response = self.client.get(self.ANOWER_GROUP)
        self.assertEqual(len(response.context['page_obj']), 0)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NPC')
        Post.objects.create(
            text='Создаем пост',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_pages(self):
        """Проверяем работу кэша главной страницы."""
        first_response = self.client.get(INDEX)
        anoter_post_note = 'Еще один пост'
        Post.objects.create(
            text=anoter_post_note,
            author=self.user
        )
        response_after_post_add = self.client.get(INDEX)
        self.assertEqual(
            first_response.content,
            response_after_post_add.content
        )
        cache.clear()
        response_after_cache_clean = self.client.get(INDEX)
        self.assertNotEqual(
            first_response.content,
            response_after_cache_clean.content
        )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.another_user = User.objects.create_user(username='author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.guest_client = Client()
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.another_user
        )
        cls.FOLLOW = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.another_user}
        )
        cls.UNFOLLOW = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.another_user}
        )

    def test_authorized_client_follow(self):
        self.authorized_client.get(
            self.FOLLOW
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user).exists()
        )

    def test_authorized_client_unfollow(self):
        Follow.objects.create(
            user=self.user,
            author=self.another_user
        )
        self.authorized_client.get(
            self.UNFOLLOW
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user
            ).exists()
        )

    def test_new_post_doesnt_shown_to_follower(self):
        response = self.authorized_client.get(FOLLOW_INDEX)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_user_cant_follow_youself(self):
        """Автор не может подписаться на себя"""
        self.authorized_client.get(
            self.FOLLOW
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.another_user,
                author=self.another_user).exists()
        )

    def test_guest_cant_follow(self):
        """Гость не может подписаться"""
        self.guest_client.get(
            self.FOLLOW
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.another_user).exists()
        )


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
        cls.ADD_COMMENT = reverse(
            'posts:add_comment',
            kwargs={
                'post_id': cls.post.id}
        )

    def test_add_comment_guest(self):
        """Комментарий не появляется в базе после добавления гостем"""
        comments_before = set(self.post.comments.all())
        form_data = {
            'text': COMMENT_TEXT
        }
        self.guest_client.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        comments_after = set(Comment.objects.filter(post=self.post))
        list_diff = comments_before ^ comments_after
        self.assertEqual(len(list_diff), 0)
