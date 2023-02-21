from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test-slug",
            description="Тестовый текст",
        )
        cls.test_user = User.objects.create_user(
            username="test1",
            email="test@test.ru",
            password="testpwd",
        )

    def setUp(self):
        cache.clear()
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Проверяет кеширование страницы index."""
        response1 = self.authorized_client.get(reverse("posts:index"))
        Post.objects.create(
            text="Новый пост",
            author=self.test_user,
            group=self.group,
        )
        response2 = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse("posts:index"))
        self.assertNotEqual(response3.content, response2.content)
