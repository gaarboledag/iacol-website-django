from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import resolve

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

def append_slash_redirect(request, path):
    """Redirect URLs without trailing slash to URLs with trailing slash"""
    return redirect(path + '/')

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('apps.api.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('agents/', include('apps.agents.urls')),
    path('payments/', include('apps.payments.urls')),
    path('', include('apps.authentication.urls')),
    prefix_default_language=False
)

# Redirect URLs without trailing slash to URLs with trailing slash
urlpatterns += [
    re_path(r'^(?P<path>.*[^/])$', append_slash_redirect),
]

# Catch-all debe ir AL FINAL para no interferir con rutas válidas
urlpatterns += [
    path('<path:undefined_path>', RedirectView.as_view(url='/'), name='redirect-to-home'),
]

# Servir archivos media en desarrollo y producción (temporal para testing)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

