from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {'text': 'Текст публикации', 'group': 'Группа'}
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Tекст нового поста'
        }
