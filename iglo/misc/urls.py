from django.urls import path

from misc.views import HomeView, RulesView, ContactView

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('rules', RulesView.as_view(), name="rules"),
    path('contact', ContactView.as_view(), name="contact"),
]
