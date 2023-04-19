from posts.forms import PostForm
from posts.models import Post, User, Group
from django.test import Client, TestCase
from django.urls import reverse


class PostFormTests(TestCase):
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
            text='Тестовый текст',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostFormTests.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает запись"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст нового поста',
            'group': PostFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, PostFormTests.group)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username':
                                     self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit_form(self):
        """Валидная форма редактирует запись"""
        posts_count = Post.objects.count()
        some_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание 2',
        )
        new_form_data = {
            'text': 'Текст измененного поста',
            'group': some_group.id
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=new_form_data,
            follow=True
        )
        edited_post = response.context['post']
        old_group_response = self.authorized_client_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        new_group_response = self.authorized_client_author.get(
            reverse('posts:group_list', args=(some_group.slug,))
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edited_post.text, new_form_data['text'])
        self.assertEqual(edited_post.group, some_group)
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 0)
        self.assertEqual(
            new_group_response.context['page_obj'].paginator.count, 1)
