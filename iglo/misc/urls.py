from django.urls import path

from misc.views import HomeView, RulesView, ContactView, ReviewsView, ResultTableFaqView

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('rules', RulesView.as_view(), name="rules"),
    path('contact', ContactView.as_view(), name="contact"),
    path('reviews', ReviewsView.as_view(), name="reviews"),
    path('how-to-read-result-tables', ResultTableFaqView.as_view(), name='result_tables_faq')
]
