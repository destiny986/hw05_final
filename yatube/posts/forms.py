from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        widgets = {
            "text": forms.Textarea(
                attrs={"cols": 80, "rows": 10, "class": "form-control"}
            ),
            "group": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(
                attrs={"cols": 80, "rows": 10, "class": "form-control"}
            ),
        }
