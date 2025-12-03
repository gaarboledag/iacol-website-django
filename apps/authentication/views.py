from django.shortcuts import render
from django.http import HttpResponse
from apps.agents.models import Agent, UserSubscription
from blog.models import BlogPost
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page
from django.urls import reverse


def home(request):
    """Página principal del sitio"""
    return render(request, 'home.html')


def about(request):
    """Página sobre nosotros"""
    return render(request, 'about.html')


def contact(request):
    """Página de contacto"""
    return render(request, 'contact.html')


# @ratelimit(key='ip', rate='10/m', method='GET')  # Temporarily disabled due to Redis issues
def solutions(request):
    """Página pública de Soluciones con listado de agentes"""
    try:
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            # Admines ven todos los agentes activos sin importar flags
            agents = Agent.objects.filter(is_active=True).select_related('category')
        else:
            agents = Agent.objects.filter(is_active=True, show_in_solutions=True).select_related('category')
        user_subscriptions = []
        if request.user.is_authenticated:
            user_subscriptions = list(
                UserSubscription.objects.filter(user=request.user, status='active')
                .values_list('agent_id', flat=True)
            )
    except Exception as e:
        # Si hay error de base de datos, mostrar página sin datos
        agents = []
        user_subscriptions = []
        print(f"Database error in solutions view: {e}")  # Para debugging

    return render(request, 'solutions.html', {
        'agents': agents,
        'user_subscriptions': user_subscriptions,
    })


def resources(request):
    """Página pública de Recursos"""
    blog_posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')[:6]  # Últimos 6 posts
    return render(request, 'resources.html', {
        'blog_posts': blog_posts
    })


def findpartai_landing(request):
    """Página de landing para FindPartAi"""
    return render(request, 'findpartai_landing.html')

def mechai_landing(request):
    """Página de landing para MechAI"""
    return render(request, 'mechai_landing.html')

def automotive(request):
    """Página de landing para el sector automotriz"""
    return render(request, 'automotive.html')

def masterclass_auto_ai(request):
    """Página Masterclass en Implementación de IA para Centros Automotrices"""
    return render(request, 'masterclass_auto_ai.html')


def custom_service(request):
    """Página de Servicio de Atención al Cliente con IA"""
    return render(request, 'custom_service.html')


def lucid_team(request):
    """Página del equipo de expertos en Lucid Bot"""
    return render(request, 'lucid_team.html')


def dental_ai_landing(request):
    """Página de landing para Dental AI"""
    return render(request, 'dental_ai_landing.html')


def ibague_ai_landing(request):
    """Página de landing para Agencia de IA en Ibagué"""
    return render(request, 'ibague_ai_landing.html')


def bogota_ai_landing(request):
    """Página de landing para Agencia de IA en Bogotá"""
    return render(request, 'bogota_ai_landing.html')


def cali_ai_landing(request):
    """Página de landing para Agencia de IA en Cali"""
    return render(request, 'cali_ai_landing.html')


def medellin_ai_landing(request):
    """Página de landing para Agencia de IA en Medellín"""
    return render(request, 'medellin_ai_landing.html')


def barranquilla_ai_landing(request):
    """Página de landing para Agencia de IA en Barranquilla"""
    return render(request, 'barranquilla_ai_landing.html')


def cartagena_ai_landing(request):
    """Página de landing para Agencia de IA en Cartagena"""
    return render(request, 'cartagena_ai_landing.html')


def privacy_policy(request):
    """Página de Política de Privacidad"""
    return render(request, 'privacy_policy.html')


def terms_of_service(request):
    """Página de Condiciones del Servicio"""
    return render(request, 'terms_of_service.html')


def robots_txt(request):
    """Archivo robots.txt para SEO"""
    content = """User-agent: *
Allow: /

Sitemap: https://iacol.online/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')


def sitemap(request):
    """Genera el sitemap XML"""
    from django.http import HttpResponse
    from django.urls import reverse
    from apps.agents.models import Agent

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Static pages
    static_pages = [
        'home',
        'about',
        'contact',
        'solutions',
        'resources',
        'lucid_team',
        'findpartai_landing',
        'mechai_landing',
        'automotive',
        'custom_service',
        'masterclass_auto_ai',
        'dental_ai_landing',
        'ibague_ai_landing',
        'bogota_ai_landing',
        'cali_ai_landing',
        'medellin_ai_landing',
        'barranquilla_ai_landing',
        'cartagena_ai_landing',
        'privacy_policy',
        'terms_of_service',
    ]

    for page in static_pages:
        try:
            url = request.build_absolute_uri(reverse(page))
            xml += f'<url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
        except:
            pass

    # Agents
    agents = Agent.objects.filter(is_active=True, show_in_solutions=True).order_by('id')
    for agent in agents:
        url = request.build_absolute_uri(reverse('agents:agent_detail', args=[agent.id]))
        xml += f'<url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>\n'

    # Payments
    try:
        url = request.build_absolute_uri(reverse('payments:plans'))
        xml += f'<url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    except:
        pass

    # Blog posts
    blog_posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')
    for post in blog_posts:
        url = request.build_absolute_uri(post.get_absolute_url())
        xml += f'<url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'

    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')
