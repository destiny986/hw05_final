from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Post, Group, Comment

User = get_user_model()


class CommentTests(TestCase):
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
        cls.post = Post.objects.create(
            text='Тест пост 1',
            author=cls.test_user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_unsigned_user_comment_create(self):
        '''Неавторизованный пользователь не может отправить коммент'''
        RESPONSE_ADRESS = reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}
        )
        RESPONSE_REDIR = f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        comment_count = Comment.objects.count()
        comment_data = {
            'text': 'Текст комментария',
        }
        response = self.guest_client.post(
            RESPONSE_ADRESS, data=comment_data, follow=True
        )
        self.assertRedirects(response, RESPONSE_REDIR)
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_signedin_user_comment_create(self):
        '''
        Авторизованный пользователь может отправить коммент
        Проверяет наличие созданного коммента на страцие поста
        '''
        COMMENT_ADRESS = reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}
        )
        POST_ADRESS = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        )
        comment_count = Comment.objects.count()
        comment_data = {
            'text': 'Текст комментария',
        }
        response = self.authorized_client.post(
            COMMENT_ADRESS, data=comment_data, follow=True
        )
        self.assertRedirects(response, POST_ADRESS)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        response = self.authorized_client.get(POST_ADRESS)
        latest_comment = response.context['page_obj'][0]
        comment_text = latest_comment.text
        self.assertEqual(comment_text, comment_data['text'])
