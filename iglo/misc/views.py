from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'misc/home.html'


class RulesView(TemplateView):
    template_name = 'misc/rules.html'


class ContactView(TemplateView):
    template_name = 'misc/contact.html'


class ReviewsView(TemplateView):
    template_name = 'misc/reviews.html'
