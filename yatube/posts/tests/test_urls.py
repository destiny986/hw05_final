from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group


User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.test_user = User.objects.create_user(
            username='test1',
            email='test@test.ru',
            password='testpwd',
        )
        cls.test_user2 = User.objects.create_user(
            username='test2',
            email='test2@test.ru',
            password='testpwd',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.test_user,
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизированный клиент
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизированный клиент 2
        # (для проверки редиректа в чужих постах)
        self.user2 = self.test_user2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.URL_INDEX = '/'
        self.URL_GROUP = f'/group/{self.group.slug}/'
        self.URL_PROFILE = f'/profile/{self.user.username}/'
        self.URL_POST = f'/posts/{self.post.pk}/'
        self.URL_POST_EDIT = f'/posts/{self.post.pk}/edit/'
        self.URL_CREATE = '/create/'
        self.UNAUTHORIZED_REDIRECT_POST_EDIT = (
            f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )
        self.UNAUTHORIZED_REDIRECT_CREATE = '/auth/login/?next=/create/'

    def test_unsigned_user_access(self):
        '''
        Проверяет достут к страницам и редирект
        для неавторизированных пользователей.
        '''
        url_dict = {
            self.URL_INDEX: 200,
            self.URL_GROUP: 200,
            self.URL_PROFILE: 200,
            self.URL_POST: 200,
            self.URL_POST_EDIT: 302,
            self.URL_CREATE: 302,
            '/unexisting_page/': 404,
        }
        redirect_dict = {
            self.URL_POST_EDIT: self.UNAUTHORIZED_REDIRECT_POST_EDIT,
            self.URL_CREATE: self.UNAUTHORIZED_REDIRECT_CREATE,
        }
        for address, code in url_dict.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if response.status_code == 302:
                    response_redir = self.guest_client.get(
                        address, follow=True
                    )
                    self.assertRedirects(
                        response_redir, redirect_dict[address]
                    )
                else:
                    self.assertEqual(response.status_code, code)

    def test_signed_user_access(self):
        '''Проверяет достут к страницам для авторизированных пользователей.'''
        url_dict = {
            self.URL_INDEX: 200,
            self.URL_GROUP: 200,
            self.URL_PROFILE: 200,
            self.URL_POST: 200,
            self.URL_POST_EDIT: 200,
            self.URL_CREATE: 200,
            '/unexisting_page/': 404,
        }
        for address, code in url_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_foreign_post_edit(self):
        '''
        Проверяет редирект при редактирования чужого поста
        у авторизированных пользователей.
        '''
        response = self.authorized_client2.get(self.URL_POST_EDIT, follow=True)
        self.assertRedirects(response, self.URL_POST)

    def test_urls_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        template_dict = {
            self.URL_INDEX: 'posts/index.html',
            self.URL_GROUP: 'posts/group_list.html',
            self.URL_PROFILE: 'posts/profile.html',
            self.URL_POST: 'posts/post_detail.html',
            self.URL_POST_EDIT: 'posts/create_post.html',
            self.URL_CREATE: 'posts/create_post.html',
        }
        for address, template in template_dict.items():
            cache.clear()
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
