from binhex import REASONABLY_LARGE

from django.contrib import messages
from django.contrib.auth.views import (
    LoginView as ContribLoginView,
    LogoutView as ContribLogoutView,
    PasswordResetView as ContribPasswordResetView,
    PasswordResetDoneView as ContribPasswordResetDoneView,
    PasswordResetConfirmView as ContribPasswordResetConfirmView,
    PasswordResetCompleteView as ContribPasswordResetCompleteView
)
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from accounts import texts
from accounts.forms import RegistrationForm, PasswordResetForm
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
        Player.objects.create(
            user=user,
            nick=form.cleaned_data["nick"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            rank=form.cleaned_data["rank"],
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            texts.REGISTRATION_SUCCESS,
        )
        return super().form_valid(form)


class LoginView(ContribLoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        try:
            return reverse("player-detail", kwargs={"slug": self.request.user.player.nick})
        except Player.DoesNotExist:
            return super().get_success_url()


class LogoutView(ContribLogoutView):
    next_page = "/"


class PasswordResetView(ContribPasswordResetView):
    form_class = PasswordResetForm
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetDoneView(ContribPasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(ContribPasswordResetConfirmView):
    success_url = reverse_lazy('accounts:password_reset_complete')
    template_name = 'accounts/password_reset_confirm.html'


class PasswordResetCompleteView(ContribPasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
