from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class ViewTests(TestCase):
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
        test_posts = []
        for i in range(13):
            test_post = Post(
                text=f"Тест пост №{i+1}",
                author=cls.test_user,
                group=cls.group,
            )
            test_posts.append(test_post)
        Post.objects.bulk_create(test_posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = self.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """view-классы используют ожидаемые HTML-шаблоны."""
        test_post = Post.objects.order_by("pub_date")[0]
        templates_dict = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_posts", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.test_user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": test_post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": test_post.pk}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in templates_dict.items():
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator_records(self):
        """
        Первая и вторая страницы возвращают
        10 и 3 записей соответственно.
        """
        view_list = [
            reverse("posts:index"),
            reverse("posts:group_posts", kwargs={"slug": self.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": self.test_user.username}
            ),
        ]
        for view in view_list:
            cache.clear()
            with self.subTest(view=view):
                response10 = self.guest_client.get(view)
                response3 = self.guest_client.get(view + "?page=2")
                self.assertEqual(len(response10.context["page_obj"]), 10)
                self.assertEqual(len(response3.context["page_obj"]), 3)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        test_post = Post.objects.order_by("pub_date")[0]
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": test_post.pk})
        )
        post = response.context.get("article")
        post_text = post.text
        post_author = post.author.username
        post_group = post.group.title
        post_count = response.context.get("post_count")
        self.assertEqual(post_text, test_post.text)
        self.assertEqual(post_author, test_post.author.username)
        self.assertEqual(post_group, test_post.group.title)
        self.assertEqual(post_count, 13)

    def test_fields_type_check(self):
        """Проверяет типы полей формы в post_create и post_edit"""
        test_post = Post.objects.order_by("pub_date")[0]
        response_creat = self.authorized_client.get(
            reverse("posts:post_create")
        )
        response_edit = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": test_post.pk})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_create = response_creat.context.get(
                    "form"
                ).fields.get(value)
                form_field_edit = response_edit.context.get("form").fields.get(
                    value
                )
                self.assertIsInstance(form_field_create, expected)
                self.assertIsInstance(form_field_edit, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        test_post = Post.objects.order_by("pub_date")[0]
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": test_post.pk})
        )
        post = response.context.get("post")
        post_text = post.text
        post_author = post.author.username
        post_group = post.group.title
        self.assertEqual(post_text, test_post.text)
        self.assertEqual(post_author, test_post.author.username)
        self.assertEqual(post_group, test_post.group.title)

    def test_new_post_available(self):
        """
        Проверяет присутствие нового поста
        на страницах index, group и profile.
        """
        new_post = Post.objects.create(
            text="Новый пост",
            author=self.test_user,
            group=self.group,
        )
        adress_list = [
            reverse("posts:index"),
            reverse("posts:group_posts", kwargs={"slug": new_post.group.slug}),
            reverse(
                "posts:profile", kwargs={"username": new_post.author.username}
            ),
        ]
        for adress in adress_list:
            cache.clear()
            response = self.guest_client.get(adress)
            latest_post = response.context["page_obj"][0]
            post_text = latest_post.text
            self.assertEqual(post_text, new_post.text)

    def test_new_post_is_not_in_wrong_group(self):
        """Проверяет отсутствие нового поста на странице чужой группы"""
        new_group = Group.objects.create(
            title="Тестовое название группы2",
            slug="test-slug2",
            description="Тестовый текст2",
        )
        new_post = Post.objects.create(
            text="Новый пост",
            author=self.test_user,
            group=self.group,
        )
        response = self.guest_client.get(
            reverse("posts:group_posts", kwargs={"slug": new_group.slug})
        )
        self.assertNotIn(new_post, response.context["page_obj"])
