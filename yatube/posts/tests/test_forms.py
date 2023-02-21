from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Post, Group

User = get_user_model()


class PostCreateFormTests(TestCase):
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

    def setUp(self):
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_creation(self):
        '''Проверяет создание записи на странице create'''
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.pk,  # id группы
        }
        self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.test_user,
            ).exists()
        )

    def test_post_edit(self):
        '''Проверяет изменение записи на странице edit'''
        post = Post.objects.create(
            text='Тест пост 1',
            author=self.test_user,
            group=self.group,
        )
        post_count = Post.objects.count()
        group2 = Group.objects.create(
            title='Тестовое название группы2',
            slug='test-slug2',
            description='Тестовый текст2',
        )
        form_data = {
            'text': 'Новый текст',
            'group': group2.pk,  # id группы
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.test_user,
                pk=post.pk,
            ).exists()
        )

    def test_unsigned_user_post_create(self):
        '''Неавторизованный пользователь не может отправлять форму'''
        guest_client = Client()
        post = Post.objects.create(
            text='Тест пост 1',
            author=self.test_user,
            group=self.group,
        )
        REDIR_CREATE = '/auth/login/?next=/create/'
        REDIR_EDIT = f'/auth/login/?next=/posts/{post.pk}/edit/'
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.pk,  # id группы
        }
        redirect_dict = {
            reverse('posts:post_create'): REDIR_CREATE,
            reverse(
                'posts:post_edit', kwargs={'post_id': post.pk}
            ): REDIR_EDIT,
        }
        for adress, redir in redirect_dict.items():
            response = guest_client.post(adress, data=form_data, follow=True)
            self.assertRedirects(response, redir)
            self.assertEqual(Post.objects.count(), post_count)
