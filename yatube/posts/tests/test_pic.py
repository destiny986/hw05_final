import shutil
import tempfile

from ..models import Post, Group
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextContainsPicTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_with_pic_create(self):
        """
        Проверят создание поста с картинкой
        и отображение картинки на страницах
        """
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый заголовок",
            "group": self.group.pk,
            "image": uploaded,
        }
        self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                group=form_data["group"],
                author=self.test_user,
                image="posts/small.gif",
            ).exists()
        )
        new_post = Post.objects.all()[0]
        adress_list = [
            reverse("posts:index"),
            reverse("posts:group_posts", kwargs={"slug": new_post.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": new_post.author.username}
            ),
            reverse("posts:post_detail", kwargs={"post_id": new_post.id}),
        ]
        for adress in adress_list:
            response = self.authorized_client.get(adress)
            self.assertContains(response, "<img")
