from django import forms
from django.contrib import messages
from django.views.generic import FormView

from accounts.models import User


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField()
    nick = forms.CharField()
    rank = forms.CharField()
    ogs = forms.CharField(required=False)


class RegistrationView(FormView):
    template_name = "accounts/registration.html"
    form_class = RegistrationForm
    success_url = "/"

    def form_valid(self, form):
        User.objects.create_user(
            email=form.cleaned_data["email"], password=form.cleaned_data["password"]
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Konto zostało utworzone. Sprawdź swoją skrzynke mailową!",
        )
        return super().form_valid(form)
