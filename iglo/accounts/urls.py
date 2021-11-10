from django.urls import path

from accounts.views import RegistrationView, LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, \
    PasswordResetDoneView, PasswordResetCompleteView, PasswordAndEmailChangeView

app_name = "accounts"

urlpatterns = [
    path("registration", RegistrationView.as_view(), name="registration"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("account", PasswordAndEmailChangeView.as_view(), name="password_change"),
    path("password-reset/", PasswordResetView.as_view(), name='password_reset'),
    path("password-reset/done/", PasswordResetDoneView.as_view(), name='password_reset_done'),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path("reset/done/", PasswordResetCompleteView.as_view(), name='password_reset_complete')
]
