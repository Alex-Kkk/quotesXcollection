from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма создания новой или редактирования старой публикации."""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        required = ('text', )


class CommentForm(forms.ModelForm):
    """Форма комментария к публикации."""

    class Meta:
        model = Comment
        fields = ('text', )
        required = ('text', )

        widgets = {
            'text': forms.Textarea(attrs={'style': 'height: 100px'})
        }
