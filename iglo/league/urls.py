from django.urls import path

from league.views import SeasonsListView, SeasonDetailView, GroupDetailView, GameDetailView

urlpatterns = [
    path('seasons', SeasonsListView.as_view(), name="seasons-list"),
    path('seasons/<pk>', SeasonDetailView.as_view(), name="season-detail"),
    path('groups/<pk>', GroupDetailView.as_view(), name="group-detail"),
    path('games/<pk>', GameDetailView.as_view(), name="game-detail"),
]
