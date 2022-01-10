from django.views.generic import TemplateView

from league.models import Season


class HomeView(TemplateView):
    template_name = "misc/home.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "latest_season": Season.objects.get_latest()
        }


class RulesView(TemplateView):
    template_name = "misc/rules.html"


class ContactView(TemplateView):
    template_name = "misc/contact.html"


class ReviewsView(TemplateView):
    template_name = "misc/reviews.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seasons = Season.objects.get_seasons_with_teachers()
        context['latest_season'] = seasons[0]
        context['season_list'] = seasons
        return context
