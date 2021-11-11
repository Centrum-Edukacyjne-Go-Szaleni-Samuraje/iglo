from django.urls import path

from league.views import SeasonsListView, SeasonDetailView, GroupDetailView, GameDetailView, PlayerDetailView, PlayerUpdateView, PrepareSeasonView, GameUpdateView

urlpatterns = [
    path('seasons', SeasonsListView.as_view(), name="seasons-list"),
    path('seasons/prepare', PrepareSeasonView.as_view(), name="seasons-prepare"),
    path('seasons/<number>', SeasonDetailView.as_view(), name="season-detail"),
    path('seasons/<season_number>/<group_name>', GroupDetailView.as_view(), name="group-detail"),
    path('seasons/<season_number>/<group_name>/<black_player>-<white_player>', GameDetailView.as_view(),
         name="game-detail"),
    path('seasons/<season_number>/<group_name>/<black_player>-<white_player>/edit', GameUpdateView.as_view(),
         name="game-update"),
    path('players/<slug>', PlayerDetailView.as_view(), name="player-detail"),
    path('players/<slug>/settings', PlayerUpdateView.as_view(), name="player-settings")
]
