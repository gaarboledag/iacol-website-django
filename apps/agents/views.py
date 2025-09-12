from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Agent, UserSubscription, AgentConfiguration, AgentUsageLog, Provider
from .forms import AgentConfigurationForm, ProviderForm
from django.contrib.auth.mixins import LoginRequiredMixin

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
    
    # Get or create configuration
    configuration, created = AgentConfiguration.objects.get_or_create(
        user=request.user, 
        agent=agent,
        defaults={'configuration_data': {}}
    )

    # Get providers if enabled
    providers = []
    if hasattr(configuration, 'enable_providers') and configuration.enable_providers:
        providers = configuration.providers.all().order_by('name')

    return render(request, 'agents/agent_configure.html', {
        'agent': agent,
        'configuration': configuration,
        'providers': providers,
        'enable_providers': getattr(configuration, 'enable_providers', False),
    })

@login_required
def toggle_module(request, agent_id, module_name):
    """Activar o desactivar un módulo de configuración"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
    agent = get_object_or_404(Agent, id=agent_id)
    configuration, _ = AgentConfiguration.objects.get_or_create(
        user=request.user, 
        agent=agent,
        defaults={'configuration_data': {}}
    )
    
    # Handle different modules
    if module_name == 'providers':
        configuration.enable_providers = not getattr(configuration, 'enable_providers', False)
        configuration.save()
        return JsonResponse({
            'status': 'success', 
            'enabled': configuration.enable_providers,
            'redirect': reverse_lazy('agents:agent_configure', kwargs={'agent_id': agent.id})
        })
    
    return JsonResponse({'status': 'error', 'message': 'Módulo no encontrado'}, status=404)

class ProviderCreateView(LoginRequiredMixin, CreateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'agents/provider_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent, id=kwargs['agent_id'])
        self.configuration = get_object_or_404(
            AgentConfiguration, 
            user=request.user, 
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.agent_config = self.configuration
        messages.success(self.request, _("Proveedor agregado exitosamente."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Proveedor")
        return context

class ProviderUpdateView(LoginRequiredMixin, UpdateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'agents/provider_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.provider = self.get_object()
        self.agent = self.provider.agent_config.agent
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, _("Proveedor actualizado exitosamente."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Proveedor")
        return context

class ProviderDeleteView(LoginRequiredMixin, DeleteView):
    model = Provider
    template_name = 'agents/provider_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.provider = self.get_object()
        self.agent = self.provider.agent_config.agent
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Proveedor eliminado exitosamente."))
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context
