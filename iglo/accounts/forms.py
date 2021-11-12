from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm as ContribPasswordResetForm
from django.core.exceptions import ValidationError

from accounts import texts
from accounts.models import User
from league.models import Player


class RegistrationForm(forms.Form):
    nick = forms.SlugField(help_text=texts.NICK_HELP_TEXT, min_length=3)
    first_name = forms.CharField(label=texts.FIRST_NAME_LABEL, help_text=texts.FIRST_NAME_HELP_TEXT)
    last_name = forms.CharField(label=texts.LAST_NAME_LABEL, help_text=texts.LAST_NAME_HELP_TEXT)
    rank = forms.IntegerField(help_text=texts.RANK_HELP_TEXT, min_value=100)
    email = forms.EmailField(help_text=texts.EMAIL_HELP_TEXT)
    password = forms.CharField(
        widget=forms.PasswordInput,
        label=texts.PASSWORD_LABEL,
        help_text=texts.PASSWORD_HELP_TEXT,
    )
    agreement = forms.BooleanField(label=texts.AGREEMENT_HELP_LABEL, required=True)

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password=password)
        return password

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(texts.EMAIL_ERROR)
        return email

    def clean_nick(self):
        nick = self.cleaned_data["nick"]
        if Player.objects.filter(nick__iexact=nick).exists():
            raise forms.ValidationError(texts.NICK_ERROR)
        return nick


class PasswordAndEmailChangeForm(forms.Form):
    old_password = forms.CharField(
        label=texts.OLD_PASSWORD_LABEL,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )
    new_password1 = forms.CharField(
        required=False,
        label=texts.NEW_PASSWORD_LABEL,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        required=False,
        label=texts.CONFIRM_NEW_PASSWORD_LABEL,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    email = forms.EmailField(
        required=False,
        label=texts.NEW_EMAIL_LABEL
    )

    field_order = ['old_password', 'new_password1', 'new_password2', 'email']

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError(
                texts.PASSWORD_INCORRECT_ERROR,
                code='password_incorrect',
            )
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    texts.PASSWORD_MISMATCH_ERROR,
                    code='password_mismatch',
                )
            password_validation.validate_password(password2, self.user)
        return password2

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(texts.EMAIL_ERROR)
        return email

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        email = self.cleaned_data['email']
        if password:
            self.user.set_password(password)
        if email:
            self.user.email = email
        if commit:
            self.user.save()
        return self.user


class PasswordResetForm(ContribPasswordResetForm):
    def get_users(self, email):
        return User.objects.filter(email__iexact=email)
