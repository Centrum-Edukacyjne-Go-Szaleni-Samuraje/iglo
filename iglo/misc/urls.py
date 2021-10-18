from django.urls import path

from misc.views import HomeView, RulesView

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('rules', RulesView.as_view(), name="rules"),
]
