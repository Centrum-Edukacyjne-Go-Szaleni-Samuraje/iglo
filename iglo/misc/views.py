from django.views.generic import TemplateView

from league.models import Season, Game


class HomeView(TemplateView):
    template_name = "misc/home.html"
    tables_count = 5

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "latest_season": Season.objects.get_latest(),
            "latest_reviews": Game.objects.get_latest_reviews(current_season=True)[:self.tables_count],
            "latest_games": Game.objects.get_latest_finished(current_season=True)[:self.tables_count],
            "upcoming_games": Game.objects.get_upcoming_games()[:self.tables_count]
        }


class RulesView(TemplateView):
    template_name = "misc/rules.html"


class ContactView(TemplateView):
    template_name = "misc/contact.html"
