from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

admin.site.site_header = "IGLO Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html')),
    path('', include('league.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
