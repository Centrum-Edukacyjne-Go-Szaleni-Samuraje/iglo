from django.contrib import messages
from django.contrib.auth.views import LoginView as ContribLoginView, LogoutView as ContribLogoutView
from django.urls import reverse_lazy
from django.views.generic import FormView

from accounts.forms import RegistrationForm
from accounts.models import User
from league.models import Player


class RegistrationView(FormView):
    template_name = "accounts/registration.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        user = User.objects.create_user(
            email=form.cleaned_data["email"], password=form.cleaned_data["password"]
        )
        Player.objects.register_player(
            user=user,
            nick=form.cleaned_data["nick"],
            rank=form.cleaned_data["rank"],
            ogs=form.cleaned_data["ogs"] or form.cleaned_data["nick"],
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "Konto zostało utworzone. Możesz się zalogować.",
        )
        return super().form_valid(form)


class LoginView(ContribLoginView):
    template_name = "accounts/login.html"


class LogoutView(ContribLogoutView):
    next_page = "/"
