from django import forms
from django.contrib.auth import password_validation

from accounts import texts
from accounts.models import User
from league.models import Player


class RegistrationForm(forms.Form):
    nick = forms.SlugField(help_text=texts.NICK_HELP_TEXT)
    rank = forms.IntegerField(help_text=texts.RANK_HELP_TEXT)
    email = forms.EmailField(help_text=texts.EMAIL_HELP_TEXT)
    password = forms.CharField(
        widget=forms.PasswordInput,
        label=texts.PASSWORD_LABEL,
        help_text=texts.PASSWORD_HELP_TEXT,
    )

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password=password)
        return password

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(texts.EMAIL_ERROR)
        return email

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.filter(nick__iexact=nick).exists():
            raise forms.ValidationError(texts.NICK_ERROR)
        return nick
