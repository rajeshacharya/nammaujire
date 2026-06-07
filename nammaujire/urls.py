from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('ask/', core_views.ask_ujire_view, name='ask_ujire'),
    path('daily/', core_views.daily_hub_view, name='daily_hub'),
    path('daily/share/', core_views.submit_local_update_view, name='submit_local_update'),
    path('auth/', include('core.urls')),
    path('services/', include('services.urls')),
    path('ads/', include('ads.urls')),
    path('locations/', include('locations.urls')),
]

if settings.DEBUG or getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

