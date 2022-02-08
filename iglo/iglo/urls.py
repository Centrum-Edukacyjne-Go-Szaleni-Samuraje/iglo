import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "IGLO Administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("league.urls")),
    path("", include("misc.urls")),
    path("", include("accounts.urls", namespace="accounts")),
    path("", include("review.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
