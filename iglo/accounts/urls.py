from django.urls import path

from accounts.views import RegistrationView, LoginView, LogoutView

app_name = "accounts"

urlpatterns = [
    path("registration", RegistrationView.as_view(), name="registration"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
]
