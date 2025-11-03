from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок поста'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите ваш пост...',
                'rows': 3
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'custom-file-input',
                'style': 'width: 300px; height: 50px;',
            }),
            'public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'id': 'commentInput',
                'class': 'form-control me-2',
                'rows': 1,
                'placeholder': 'Добавь сюда комментарий',
                'style': 'max-width: 800px;'
            }),
        }
        labels = {
            'content': 'Комментарий',
        }
