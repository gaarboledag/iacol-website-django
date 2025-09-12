from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import Agent, UserSubscription, AgentConfiguration, AgentUsageLog
from .forms import AgentConfigurationForm

@login_required
def agent_list(request):
    """Lista todos los agentes disponibles"""
    if request.user.is_staff or request.user.is_superuser:
        # Admines ven todos los agentes activos
        agents = Agent.objects.filter(is_active=True)
    else:
        agents = Agent.objects.filter(is_active=True, show_in_agents=True)
    user_subscriptions = UserSubscription.objects.filter(
        user=request.user, 
        status='active'
    ).values_list('agent_id', flat=True)
    
    return render(request, 'agents/agent_list.html', {
        'agents': agents,
        'user_subscriptions': list(user_subscriptions)
    })

@login_required
def agent_detail(request, agent_id):
    """Detalle de un agente específico"""
    agent = get_object_or_404(Agent, id=agent_id)
    # Control de visibilidad: admin/staff siempre pueden ver
    if not (request.user.is_staff or request.user.is_superuser):
        is_public = agent.show_in_agents or agent.show_in_solutions
        if not is_public and request.user not in agent.allowed_users.all():
            raise Http404("Agente no disponible")
    has_subscription = UserSubscription.objects.filter(
        user=request.user, 
        agent=agent, 
        status='active'
    ).exists()
    
    return render(request, 'agents/agent_detail.html', {
        'agent': agent,
        'has_subscription': has_subscription
    })

@login_required
def agent_dashboard(request, agent_id):
    """Dashboard de estadísticas para un agente"""
    agent = get_object_or_404(Agent, id=agent_id)
    subscription = get_object_or_404(
        UserSubscription, 
        user=request.user, 
        agent=agent, 
        status='active'
    )
    
    # Estadísticas básicas
    usage_logs = AgentUsageLog.objects.filter(user=request.user, agent=agent)
    total_executions = usage_logs.count()
    successful_executions = usage_logs.filter(success=True).count()
    failed_executions = usage_logs.filter(success=False).count()
    
    # Últimas ejecuciones
    recent_executions = usage_logs.order_by('-created_at')[:10]
    
    # Configuración actual
    try:
        configuration = AgentConfiguration.objects.get(user=request.user, agent=agent)
    except AgentConfiguration.DoesNotExist:
        configuration = None
    
    return render(request, 'agents/agent_dashboard.html', {
        'agent': agent,
        'subscription': subscription,
        'total_executions': total_executions,
        'successful_executions': successful_executions,
        'failed_executions': failed_executions,
        'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
        'recent_executions': recent_executions,
        'configuration': configuration,
    })

@login_required
def agent_configure(request, agent_id):
    """Configuración de un agente"""
    agent = get_object_or_404(Agent, id=agent_id)
    subscription = get_object_or_404(
        UserSubscription, 
        user=request.user, 
        agent=agent, 
        status='active'
    )
    
    try:
        configuration = AgentConfiguration.objects.get(user=request.user, agent=agent)
    except AgentConfiguration.DoesNotExist:
        configuration = None
    
    if request.method == 'POST':
        form = AgentConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            config = form.save(commit=False)
            config.user = request.user
            config.agent = agent
            config.save()
            messages.success(request, 'Configuración guardada exitosamente.')
            return redirect('agents:agent_dashboard', agent_id=agent.id)
    else:
        form = AgentConfigurationForm(instance=configuration)
    
    return render(request, 'agents/agent_configure.html', {
        'agent': agent,
        'form': form,
        'configuration': configuration,
    })
