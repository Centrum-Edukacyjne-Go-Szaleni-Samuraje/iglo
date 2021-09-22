from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

admin.site.site_header = "IGLO Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'))
]
