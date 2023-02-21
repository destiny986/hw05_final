from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Follow, Post

User = get_user_model()


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user1 = User.objects.create_user(
            username='test1',
            email='test@test.ru',
            password='testpwd',
        )
        cls.test_user2 = User.objects.create_user(
            username='test2',
            email='test2@test.ru',
            password='testpwd',
        )

    def setUp(self):
        self.user1 = self.test_user1
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.user2 = self.test_user2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_unsigned_user_comment_create(self):
        '''
        Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок
        '''
        follow_count = Follow.objects.count()
        self.authorized_client2.get(reverse('posts:profile_follow', kwargs={'username': self.test_user1.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.test_user2,
                author=self.test_user1,
            ).exists()
        )
        self.authorized_client2.get(reverse('posts:profile_unfollow', kwargs={'username': self.test_user1.username}))
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.test_user2,
                author=self.test_user1,
            ).exists()
        )

    def test_unsigned_user_comment_create(self):
        '''
        Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        '''
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.test_user1,
        )
        Follow.objects.create(
            user=self.test_user2,
            author=self.test_user1,
        )
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        latest_post = response.context['page_obj'][0]
        self.assertEqual(new_post, latest_post)
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        self.assertNotIn(new_post, response.context['page_obj'])
