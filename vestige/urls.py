from django.contrib import admin
from django.urls import path, include  # 👈 добавьте include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)