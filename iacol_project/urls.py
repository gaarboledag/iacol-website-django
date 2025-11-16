from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import resolve
from django.contrib.sitemaps.views import sitemap
from django.utils import timezone
from django.http import HttpResponse
from .sitemaps import StaticSitemap, AgentSitemap, PaymentSitemap

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
    path('blog/', include('blog.urls')),
    path('', include('apps.authentication.urls')),
    prefix_default_language=False
)

# Health check endpoint for monitoring
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy', 'timestamp': timezone.now().isoformat()})

urlpatterns += [
    path('health/', health_check, name='health-check'),
]

# CRITICAL-004: Fixed URL patterns - More specific catch-all pattern
# Redirect URLs without trailing slash to URLs with trailing slash (but only valid ones)
urlpatterns += [
    re_path(r'^(?P<path>[^.]+)$', append_slash_redirect, name='append_slash'),
]

# CRITICAL-004: Restrictive catch-all pattern - avoid conflicts with static assets
# Only catch paths that don't look like files or API endpoints
urlpatterns += [
    re_path(r'^(?P<undefined_path>[^/.]+\/?)$', RedirectView.as_view(url='/'), name='redirect-to-home'),
]

# Static and media files are served by Nginx in production
# Only serve in development
if settings.DEBUG:
    # Serve static files from STATICFILES_DIRS in development
    for static_dir in settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=static_dir)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
