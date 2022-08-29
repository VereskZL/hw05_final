from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_subject(self):
        data = self.cleaned_data['text']

        if '' in data.lower():
            raise forms.ValidationError('А что читать то?')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
