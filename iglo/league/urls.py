from django.urls import path

from league.views import SeasonsListView, SeasonDetailView, GroupDetailView, GameDetailView, PlayerDetailView, PlayerSettingsView, PrepareSeasonView
, GameUpdateView

urlpatterns = [
    path('seasons', SeasonsListView.as_view(), name="seasons-list"),
    path('seasons/prepare', PrepareSeasonView.as_view(), name="seasons-prepare"),
    path('seasons/<number>', SeasonDetailView.as_view(), name="season-detail"),
    path('seasons/<season_number>/<group_name>', GroupDetailView.as_view(), name="group-detail"),
    path('seasons/<season_number>/<group_name>/<black_player>-<white_player>', GameDetailView.as_view(),
         name="game-detail"),
    path('seasons/<season_number>/<group_name>/<black_player>-<white_player>/edit', GameUpdateView.as_view(),
         name="game-update"),
    path('player/<slug>', PlayerDetailView.as_view(), name="player-detail"),
    path('player/<nick>/settings', PlayerSettingsView.as_view(), name="player-settings")
]
