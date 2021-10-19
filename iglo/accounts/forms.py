from django import forms

from accounts.models import User


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(min_length=8)
    nick = forms.CharField()
    rank = forms.CharField()
    ogs = forms.CharField(required=False)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten e-mail jest już zajęty.")
        return email

