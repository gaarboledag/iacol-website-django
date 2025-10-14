from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('apps.api.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('agents/', include('apps.agents.urls')),
    path('payments/', include('apps.payments.urls')),
    path('', include('apps.authentication.urls')),
    
    # Redirección para cualquier URL no encontrada
    path('<path:undefined_path>', RedirectView.as_view(url='/'), name='redirect-to-home'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
