import debug_toolbar
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "IGLO Administration"

localized_patterns = i18n_patterns(
    path("", include("league.urls")),
    path("", include("misc.urls")),
    path("", include("accounts.urls", namespace="accounts")),
    path("", include("review.urls")),
    prefix_default_language=False,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__debug__/", include(debug_toolbar.urls)),
] + localized_patterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

