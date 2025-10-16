from django import forms
from .models import Post


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
                'rows': 5
            }),
            'public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }