from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('users.urls')),
    path('intake/', include('intake.urls')),
    path('plan/', include('plans.urls')),
    path('log/', include('logs.urls', namespace='logs')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
