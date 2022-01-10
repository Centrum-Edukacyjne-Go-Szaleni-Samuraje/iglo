from django.urls import path

from league.views import SeasonsListView, SeasonDetailView, GroupDetailView, GameDetailView, PlayerDetailView, \
    PlayerUpdateView, PrepareSeasonView, GameUpdateView, SeasonExportCSVView, TeachersListView

urlpatterns = [
    path('seasons', SeasonsListView.as_view(), name="seasons-list"),
    path('seasons/prepare', PrepareSeasonView.as_view(), name="seasons-prepare"),
    path('seasons/<int:number>', SeasonDetailView.as_view(), name="season-detail"),
    path('seasons/<int:number>/export', SeasonExportCSVView.as_view(), name="season-export"),
    path('seasons/<int:number>/reviews', TeachersListView.as_view(), name="teachers-list"),
    path('seasons/<int:season_number>/<group_name>', GroupDetailView.as_view(), name="group-detail"),
    path('seasons/<int:season_number>/<group_name>/<black_player>-<white_player>', GameDetailView.as_view(),
         name="game-detail"),
    path('seasons/<int:season_number>/<group_name>/<bye_player>', GameDetailView.as_view(), name='bye-game-detail'),
    path('seasons/<int:season_number>/<group_name>/<black_player>-<white_player>/edit', GameUpdateView.as_view(),
         name="game-update"),
    path('players/<slug>', PlayerDetailView.as_view(), name="player-detail"),
    path('players/<slug>/settings', PlayerUpdateView.as_view(), name="player-settings"),
]
