from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 10,
        )

    def test_models_have_correct_object_names(self):
        '''Проверяем, что у моделей корректно работает __str__.'''
        test_dict = {
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.post: PostModelTest.post.text[:15],
        }
        for field, expected_value in test_dict.items():
            with self.subTest(field=field):
                self.assertEqual(field.__str__(), expected_value)
