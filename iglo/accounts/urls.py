from django.urls import path

from accounts.views import RegistrationView

urlpatterns = [
    path('registration', RegistrationView.as_view(), name="registration"),
]
