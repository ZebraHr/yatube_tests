from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django import forms

from ..models import Post, User, Group

TEST_POSTS_NUM = 13


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст длиной не менее 15 символов',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны страниц правильно отображают посты"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username':
                                             PostPagesTests.user.username}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_object = response.context['page_obj'][0]
                post_author = first_object.author
                post_text = first_object.text
                post_pub_date = first_object.pub_date
                self.assertEqual(post_author, PostPagesTests.user)
                self.assertEqual(post_text, PostPagesTests.post.text)
                self.assertEqual(post_pub_date, PostPagesTests.post.pub_date)

    def test__group_posts_page_shows_correct_context(self):
        """Шаблон страницы group_posts сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        group_test = response.context['group']
        self.assertEqual(group_test.title, PostPagesTests.group.title)
        self.assertEqual(group_test.slug, PostPagesTests.group.slug)
        self.assertEqual(group_test.description,
                         PostPagesTests.group.description)

    def test_group_page_contains_group_records(self):
        """На странице group оттображены посты группы"""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        group_post = response.context['page_obj'][0]
        expected = response.context['group']
        self.assertEqual(str(group_post.group), expected.title)

    def test__profile_page_shows_correct_context(self):
        """Шаблон страницы profile сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user.username}))
        author_test = response.context['author']
        self.assertEqual(str(author_test.username),
                         PostPagesTests.user.username)

    def test_profile_page_contains_auth_records(self):
        """На странице profile отображены посты автора"""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username':
                                     PostPagesTests.user.username}))
        auth_post = response.context['page_obj'][0]
        expected = response.context['author']
        self.assertEqual(str(auth_post.author), expected.username)

    def test_post_detail_shows_correct_content(self):
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        test_post = response.context['post']
        self.assertEqual(test_post.author, PostPagesTests.user)
        self.assertEqual(test_post.text, PostPagesTests.post.text)
        self.assertEqual(test_post.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(test_post.group, PostPagesTests.group)

    def test_create_post_page_contains_correct_form(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_contains_correct_form(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post(self):
        """Проверяем отображение нового поста"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.post.author}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                posts = response.context['page_obj']
                self.assertIn(PostPagesTests.post, posts)

    def test_new_post_not_in_wrong_group(self):
        """Созданный пост не попал в группу, для которой не был предназначен"""
        some_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание 2',
        )
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug":
                                                some_group.slug}))
        some_group_posts = response.context['page_obj']
        self.assertNotIn(PostPagesTests.post, some_group_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.list_post = [
            Post(
                author=cls.user,
                text=f'Тестовый пост {post_num}',
                group=cls.group,
            )
            for post_num in range(TEST_POSTS_NUM)
        ]
        Post.objects.bulk_create(cls.list_post)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_main_page_contains_ten_records(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_SHOWN)
