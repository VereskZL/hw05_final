from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()
INDEX = '/'
FAKE = '/fake_page/'
CREATE = '/create/'


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.some_user = User.objects.create_user(username='NPS')
        cls.user = User.objects.create_user(username='VIP_NPS')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.GROUP = (f'/group/{cls.group.slug}/')
        cls.PROFILE = (f'/profile/{cls.post.author}/')
        cls.POST_ID = (f'/posts/{cls.post.id}/')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.some_user)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response_list = [
            INDEX,
            self.GROUP,
            self.PROFILE,
        ]
        for response_one in response_list:
            response = self.guest_client.get(response_one)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_added_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованому пользователю."""
        response = self.authorized_client.get(CREATE)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX: 'posts/index.html',
            self.GROUP: 'posts/group_list.html',
            self.PROFILE: 'posts/profile.html',
            self.POST_ID: 'posts/post_detail.html',
            CREATE: 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
