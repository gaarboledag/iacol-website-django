from django.shortcuts import render
from apps.agents.models import Agent, UserSubscription


def home(request):
    """Página principal del sitio"""
    return render(request, 'home.html')


def about(request):
    """Página sobre nosotros"""
    return render(request, 'about.html')


def contact(request):
    """Página de contacto"""
    return render(request, 'contact.html')


def solutions(request):
    """Página pública de Soluciones con listado de agentes"""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        # Admines ven todos los agentes activos sin importar flags
        agents = Agent.objects.filter(is_active=True)
    else:
        agents = Agent.objects.filter(is_active=True, show_in_solutions=True)
    user_subscriptions = []
    if request.user.is_authenticated:
        user_subscriptions = list(
            UserSubscription.objects.filter(user=request.user, status='active')
            .values_list('agent_id', flat=True)
        )

    return render(request, 'solutions.html', {
        'agents': agents,
        'user_subscriptions': user_subscriptions,
    })


def resources(request):
    """Página pública de Recursos"""
    return render(request, 'resources.html')


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
def dental_ai_landing(request):
    """Página de landing para Dental AI"""
    return render(request, 'dental_ai_landing.html')
    return render(request, 'lucid_team.html')
