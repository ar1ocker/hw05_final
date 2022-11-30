from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст поста'}
        help_texts = {'text': 'Текст нового поста',
                      'group': 'Группа к которой будет относится текст'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
