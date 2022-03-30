from django import forms
from django.urls import reverse_lazy

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста:'),
            'group': ('Выберите группу'),
        }
    success_url = reverse_lazy('posts:profile')
    template_name = 'posts/create_post.html'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
