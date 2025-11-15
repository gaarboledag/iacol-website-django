from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import Agent, UserSubscription, AgentConfiguration, AgentUsageLog, Provider, ProviderCategory, Brand, Product, ProductCategory, ProductBrand, AutomotiveCenterInfo
from .forms import AgentConfigurationForm, ProviderForm, ProviderCategoryForm, BrandForm, ProductForm, ProductCategoryForm, ProductBrandForm, AutomotiveCenterInfoForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Sum, Q

@login_required
@ratelimit(key='user', rate='20/m', method='GET')
def agent_list(request):
    """Lista todos los agentes disponibles con paginación"""
    # MEDIUM-001: Corrección de cache key para incluir parámetros relevantes
    page = request.GET.get('page', '1')
    search_query = request.GET.get('search', '')
    # Include user permissions and search query in cache key
    cache_key = f'agent_list_{request.user.is_staff or request.user.is_superuser}_page_{page}_search_{search_query}'
    agents = cache.get(cache_key)

    if agents is None:
        query = Agent.objects.filter(is_active=True).select_related('category')
        
        if request.user.is_staff or request.user.is_superuser:
            # Admines ven todos los agentes activos
            pass  # query already set above
        else:
            query = query.filter(show_in_agents=True)
            
        # Apply search if provided
        if search_query:
            query = query.filter(name__icontains=search_query)
            
        agents = list(query)
        cache.set(cache_key, agents, 300)  # Cache for 5 minutes

    # Paginación
    paginator = Paginator(agents, 12)  # 12 agentes por página
    try:
        agents_page = paginator.page(page)
    except PageNotAnInteger:
        agents_page = paginator.page(1)
    except EmptyPage:
        agents_page = paginator.page(paginator.num_pages)

    user_subscriptions = UserSubscription.objects.filter(
        user=request.user,
        status='active'
    ).values_list('agent_id', flat=True)

    return render(request, 'agents/agent_list.html', {
        'agents': agents_page,
        'user_subscriptions': list(user_subscriptions)
    })

@login_required
def agent_detail(request, agent_id):
    """Detalle de un agente específico"""
    agent = get_object_or_404(Agent.objects.select_related('category'), id=agent_id)
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
    agent = get_object_or_404(Agent.objects.select_related('category'), id=agent_id)
    subscription = get_object_or_404(
        UserSubscription,
        user=request.user,
        agent=agent,
        status='active'
    )
    
    # CRITICAL-001: Optimización crítica - Usar annotate para agregaciones en una sola query
    cache_key = f'agent_dashboard_stats_{request.user.id}_{agent_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Query optimizada con annotate para evitar N+1
        usage_logs = AgentUsageLog.objects.filter(
            user=request.user, 
            agent=agent,
            created_at__date=timezone.now().date()
        ).aggregate(
            total_executions=Count('id'),
            successful_executions=Count('id', filter=Q(success=True)),
            failed_executions=Count('id', filter=Q(success=False))
        )
        
        # Calcular success rate
        total = usage_logs['total_executions'] or 0
        successful = usage_logs['successful_executions'] or 0
        failed = usage_logs['failed_executions'] or 0
        
        stats = {
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
        
        # Cache por 5 minutos
        cache.set(cache_key, stats, 300)
    
    # Últimas ejecuciones con select_related para mejor performance
    recent_executions = AgentUsageLog.objects.filter(
        user=request.user, agent=agent
    ).select_related('agent').order_by('-created_at')[:10]
    
    # Configuración actual
    try:
        configuration = AgentConfiguration.objects.select_related('agent').get(
            user=request.user, 
            agent=agent
        )
    except AgentConfiguration.DoesNotExist:
        configuration = None
    
    return render(request, 'agents/agent_dashboard.html', {
        'agent': agent,
        'subscription': subscription,
        'total_executions': stats['total_executions'],
        'successful_executions': stats['successful_executions'],
        'failed_executions': stats['failed_executions'],
        'success_rate': stats['success_rate'],
        'recent_executions': recent_executions,
        'configuration': configuration,
    })

@login_required
def agent_configure(request, agent_id):
    """Configuración de un agente"""
    agent = get_object_or_404(Agent.objects.select_related('category'), id=agent_id)
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

    # Get providers if enabled with paginación
    providers_page = None
    if hasattr(configuration, 'enable_providers') and configuration.enable_providers:
        providers_qs = configuration.providers.select_related('category').prefetch_related('brands').all().order_by('name')
        paginator = Paginator(providers_qs, 10)  # 10 proveedores por página
        page = request.GET.get('providers_page')
        try:
            providers_page = paginator.page(page)
        except PageNotAnInteger:
            providers_page = paginator.page(1)
        except EmptyPage:
            providers_page = paginator.page(paginator.num_pages)

    # Get products if enabled con paginación
    products_page = None
    if hasattr(configuration, 'enable_products') and configuration.enable_products:
        products_qs = configuration.products.select_related('category', 'brand').all().order_by('-created_at')
        paginator = Paginator(products_qs, 10)  # 10 productos por página
        page = request.GET.get('products_page')
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

    # Get automotive center info if enabled
    automotive_info = None
    if hasattr(configuration, 'enable_automotive_info') and configuration.enable_automotive_info:
        automotive_info = getattr(configuration, 'automotive_center_info', None)

    return render(request, 'agents/agent_configure.html', {
        'agent': agent,
        'configuration': configuration,
        'providers': providers_page,
        'products': products_page,
        'automotive_info': automotive_info,
        'enable_providers': getattr(configuration, 'enable_providers', False),
        'enable_products': getattr(configuration, 'enable_products', False),
        'enable_automotive_info': getattr(configuration, 'enable_automotive_info', False),
    })

@login_required
def toggle_module(request, agent_id, module_name):
    """Activar o desactivar un módulo de configuración"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    agent = get_object_or_404(Agent.objects.select_related('category'), id=agent_id)
    configuration, _ = AgentConfiguration.objects.get_or_create(
        user=request.user,
        agent=agent,
        defaults={'configuration_data': {}}
    )

    # Handle different modules
    if module_name == 'providers':
        if 'MechAI' not in agent.name:
            return JsonResponse({'status': 'error', 'message': 'La gestión de proveedores solo está disponible para agentes MechAI'}, status=403)
        configuration.enable_providers = not getattr(configuration, 'enable_providers', False)
        configuration.save()
        return JsonResponse({
            'status': 'success',
            'enabled': configuration.enable_providers,
            'redirect': reverse_lazy('agents:agent_configure', kwargs={'agent_id': agent.id})
        })
    elif module_name == 'products':
        if 'MechAI' not in agent.name:
            return JsonResponse({'status': 'error', 'message': 'La gestión de productos solo está disponible para agentes MechAI'}, status=403)
        configuration.enable_products = not getattr(configuration, 'enable_products', False)
        configuration.save()
        return JsonResponse({
            'status': 'success',
            'enabled': configuration.enable_products,
            'redirect': reverse_lazy('agents:agent_configure', kwargs={'agent_id': agent.id})
        })
    elif module_name == 'automotive_info':
        if 'MechAI' not in agent.name:
            return JsonResponse({'status': 'error', 'message': 'La información del centro automotriz solo está disponible para agentes MechAI'}, status=403)
        configuration.enable_automotive_info = not getattr(configuration, 'enable_automotive_info', False)
        configuration.save()
        return JsonResponse({
            'status': 'success',
            'enabled': configuration.enable_automotive_info,
            'redirect': reverse_lazy('agents:agent_configure', kwargs={'agent_id': agent.id})
        })

    return JsonResponse({'status': 'error', 'message': 'Módulo no encontrado'}, status=404)

class ProviderCreateView(LoginRequiredMixin, CreateView):
    model = Provider
    form_class = ProviderForm
    template_name = 'agents/provider_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = AgentConfiguration.objects.get(
            user=self.request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Proveedor creado exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear el proveedor. Por favor intente nuevamente."))
            return self.form_invalid(form)

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
        self.agent_config = self.provider.agent_config  # Añade esta línea
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):  # Añade este método
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs
    
    def form_valid(self, form):
        try:
            messages.success(self.request, _("Proveedor actualizado exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar el proveedor. Por favor intente nuevamente."))
            return self.form_invalid(form)
    
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
        try:
            messages.success(request, _("Proveedor eliminado exitosamente."))
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(request, _("Error al eliminar el proveedor. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id}))
    
    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class ProviderCategoryListView(LoginRequiredMixin, ListView):
    model = ProviderCategory
    template_name = 'agents/provider_category_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return ProviderCategory.objects.filter(agent_config__agent=self.agent)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class ProductCategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'agents/product_category_list.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ProductCategory.objects.filter(agent_config__agent=self.agent)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'agents/product_category_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        # Get or create the agent configuration
        self.agent_config, _ = AgentConfiguration.objects.get_or_create(
            user=self.request.user,
            agent=self.agent,
            defaults={'configuration_data': {}}
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Categoría de producto agregada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear la categoría. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:product_category_list', kwargs={'agent_id': self.agent.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Categoría de Producto")
        return context

class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'agents/product_category_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = self.get_object()
        self.agent = self.category.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            messages.success(self.request, _("Categoría de producto actualizada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar la categoría. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:product_category_list', kwargs={'agent_id': self.agent.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.category.agent_config
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Categoría de Producto")
        return context

class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'agents/product_category_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = self.get_object()
        self.agent = self.category.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            messages.success(self.request, _("Categoría de producto eliminada exitosamente."))
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al eliminar la categoría. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:product_category_list', kwargs={'agent_id': self.agent.id}))

    def get_success_url(self):
        return reverse_lazy('agents:product_category_list', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class AutomotiveCenterInfoCreateView(LoginRequiredMixin, CreateView):
    model = AutomotiveCenterInfo
    form_class = AutomotiveCenterInfoForm
    template_name = 'agents/automotive_center_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = AgentConfiguration.objects.get(
            user=self.request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Información del centro automotriz creada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear la información del centro. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Configurar Centro Automotriz")
        return context

class AutomotiveCenterInfoUpdateView(LoginRequiredMixin, UpdateView):
    model = AutomotiveCenterInfo
    form_class = AutomotiveCenterInfoForm
    template_name = 'agents/automotive_center_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.automotive_info = self.get_object()
        self.agent = self.automotive_info.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            messages.success(self.request, _("Información del centro automotriz actualizada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar la información del centro. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Centro Automotriz")
        return context

class ProductBrandListView(LoginRequiredMixin, ListView):
    model = ProductBrand
    template_name = 'agents/product_brand_list.html'
    context_object_name = 'product_brands'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = get_object_or_404(
            AgentConfiguration,
            user=request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ProductBrand.objects.filter(agent_config=self.agent_config).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['agent_config'] = self.agent_config
        return context

class ProductBrandCreateView(LoginRequiredMixin, CreateView):
    model = ProductBrand
    form_class = ProductBrandForm
    template_name = 'agents/product_brand_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = get_object_or_404(
            AgentConfiguration,
            user=self.request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Marca de producto creada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear la marca. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:product_brand_list', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Marca de Producto")
        return context

class ProductBrandUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductBrand
    form_class = ProductBrandForm
    template_name = 'agents/product_brand_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.brand = self.get_object()
        self.agent = self.brand.agent_config.agent
        self.agent_config = self.brand.agent_config
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def form_valid(self, form):
        try:
            messages.success(self.request, _("Marca de producto actualizada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar la marca. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:product_brand_list', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Marca de Producto")
        return context

class ProductBrandDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductBrand
    template_name = 'agents/product_brand_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.brand = self.get_object()
        self.agent = self.brand.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, _("Marca de producto eliminada exitosamente."))
            return response
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(request, _("Error al eliminar la marca. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:product_brand_list', kwargs={'agent_id': self.agent.id}))

    def get_success_url(self):
        return reverse_lazy('agents:product_brand_list', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class ProviderCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProviderCategory
    form_class = ProviderCategoryForm
    template_name = 'agents/provider_category_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        # Get or create the agent configuration
        self.agent_config, _ = AgentConfiguration.objects.get_or_create(
            user=self.request.user,
            agent=self.agent,
            defaults={'configuration_data': {}}
        )
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Categoría de proveedor agregada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear la categoría. Por favor intente nuevamente."))
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:provider_category_list', kwargs={'agent_id': self.agent.id})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Categoría de Proveedor")
        return context

class ProviderCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProviderCategory
    form_class = ProviderCategoryForm
    template_name = 'agents/provider_category_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.category = self.get_object()
        self.agent = self.category.agent_config.agent  # Fixed: Access agent through agent_config
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            messages.success(self.request, _("Categoría de proveedor actualizada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar la categoría. Por favor intente nuevamente."))
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:provider_category_list', kwargs={'agent_id': self.agent.id})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.category.agent_config
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Categoría de Proveedor")
        return context

class ProviderCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProviderCategory
    template_name = 'agents/provider_category_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.category = self.get_object()
        self.agent = self.category.agent_config.agent  # Fixed: Access agent through agent_config
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(self.request, _("Categoría de proveedor eliminada exitosamente."))
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al eliminar la categoría. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:provider_category_list', kwargs={'agent_id': self.agent.id}))
    
    def get_success_url(self):
        return reverse_lazy('agents:provider_category_list', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class BrandListView(LoginRequiredMixin, ListView):
    model = Brand
    template_name = 'agents/brand_list.html'
    context_object_name = 'brands'
    
    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = get_object_or_404(
            AgentConfiguration,
            user=request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Brand.objects.filter(agent_config=self.agent_config).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['agent_config'] = self.agent_config
        return context

class BrandCreateView(LoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'agents/brand_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = get_object_or_404(
            AgentConfiguration,
            user=request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs
    
    def form_valid(self, form):
        try:
            form.instance.agent_config = self.agent_config
            messages.success(self.request, _("Marca creada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear la marca. Por favor intente nuevamente."))
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:brand_list', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Marca")
        return context

class BrandUpdateView(LoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'agents/brand_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.brand = self.get_object()
        self.agent = self.brand.agent_config.agent
        self.agent_config = self.brand.agent_config
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs
    
    def form_valid(self, form):
        try:
            messages.success(self.request, _("Marca actualizada exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar la marca. Por favor intente nuevamente."))
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('agents:brand_list', kwargs={'agent_id': self.agent.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Marca")
        return context

class BrandDeleteView(LoginRequiredMixin, DeleteView):
    model = Brand
    template_name = 'agents/brand_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.brand = self.get_object()
        self.agent = self.brand.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, _("Marca eliminada exitosamente."))
            return response
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(request, _("Error al eliminar la marca. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:brand_list', kwargs={'agent_id': self.agent.id}))

    def get_success_url(self):
        return reverse_lazy('agents:brand_list', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'agents/product_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.agent = get_object_or_404(Agent.objects.select_related('category'), id=kwargs['agent_id'])
        self.agent_config = AgentConfiguration.objects.get(
            user=self.request.user,
            agent=self.agent
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def form_valid(self, form):
        form.instance.agent_config = self.agent_config

        # CRITICAL-003: Memory leak fix - Handle URL-based image upload safely with streaming
        if hasattr(form.instance, 'image_upload_method') and form.cleaned_data.get('image_upload_method') == 'url':
            image_url = form.cleaned_data.get('image_url')
            if image_url:
                try:
                    import requests
                    from django.core.files.base import ContentFile
                    import os
                    from urllib.parse import urlparse
                    import tempfile

                    # CRITICAL-003: Use streaming to prevent memory leaks
                    response = requests.get(image_url, timeout=10, stream=True, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()

                    # Check content length if available
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                        raise ValueError("File too large (max 10MB)")

                    # Validate content type
                    content_type = response.headers.get('content-type', '')
                    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                    if content_type and not any(allowed_type in content_type.lower() for allowed_type in allowed_types):
                        raise ValueError("Invalid file type")

                    # Get file extension from URL or content-type
                    parsed_url = urlparse(image_url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename or '.' not in filename:
                        ext = '.jpg'  # default
                        if 'png' in content_type:
                            ext = '.png'
                        elif 'gif' in content_type:
                            ext = '.gif'
                        elif 'webp' in content_type:
                            ext = '.webp'
                        filename = f"product_{form.instance.title.replace(' ', '_')}{ext}"

                    # CRITICAL-003: Use temporary file with streaming to prevent memory leaks
                    temp_file_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                            total_size = 0
                            # CRITICAL-003: Stream content in chunks to prevent memory usage
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    total_size += len(chunk)
                                    # Strict size limit check during streaming
                                    if total_size > 10 * 1024 * 1024:  # 10MB limit
                                        raise ValueError("File too large (max 10MB)")
                                    temp_file.write(chunk)
                            
                            temp_file.seek(0)
                            temp_file_path = temp_file.name
                            form.instance.image.save(filename, ContentFile(temp_file.read()), save=False)

                        form.instance.image_url = image_url

                    finally:
                        # CRITICAL-003: Ensure temp file is cleaned up
                        if temp_file_path and os.path.exists(temp_file_path):
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass

                except requests.RequestException as e:
                    form.add_error('image_url', f"Error al descargar la imagen: {str(e)}")
                    return self.form_invalid(form)
                except Exception as e:
                    form.add_error('image_url', f"Error al procesar la imagen: {str(e)}")
                    return self.form_invalid(form)

        try:
            messages.success(self.request, _("Producto creado exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al crear el producto. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Agregar Producto")
        return context

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'agents/product_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = self.get_object()
        self.agent = self.product.agent_config.agent
        self.agent_config = self.product.agent_config
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['agent_config'] = self.agent_config
        return kwargs

    def form_valid(self, form):
        # CRITICAL-003: Memory leak fix - Handle URL-based image upload safely with streaming
        if hasattr(form.instance, 'image_upload_method') and form.cleaned_data.get('image_upload_method') == 'url':
            image_url = form.cleaned_data.get('image_url')
            if image_url and image_url != getattr(self.product, 'image_url', None):
                try:
                    import requests
                    from django.core.files.base import ContentFile
                    import os
                    from urllib.parse import urlparse
                    import tempfile

                    # CRITICAL-003: Use streaming to prevent memory leaks
                    response = requests.get(image_url, timeout=10, stream=True, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()

                    # Check content length if available
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                        raise ValueError("File too large (max 10MB)")

                    # Validate content type
                    content_type = response.headers.get('content-type', '')
                    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                    if content_type and not any(allowed_type in content_type.lower() for allowed_type in allowed_types):
                        raise ValueError("Invalid file type")

                    # Get file extension from URL or content-type
                    parsed_url = urlparse(image_url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename or '.' not in filename:
                        ext = '.jpg'  # default
                        if 'png' in content_type:
                            ext = '.png'
                        elif 'gif' in content_type:
                            ext = '.gif'
                        elif 'webp' in content_type:
                            ext = '.webp'
                        filename = f"product_{form.instance.title.replace(' ', '_')}{ext}"

                    # CRITICAL-003: Use temporary file with streaming to prevent memory leaks
                    temp_file_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                            total_size = 0
                            # CRITICAL-003: Stream content in chunks to prevent memory usage
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    total_size += len(chunk)
                                    # Strict size limit check during streaming
                                    if total_size > 10 * 1024 * 1024:  # 10MB limit
                                        raise ValueError("File too large (max 10MB)")
                                    temp_file.write(chunk)
                            
                            temp_file.seek(0)
                            temp_file_path = temp_file.name
                            form.instance.image.save(filename, ContentFile(temp_file.read()), save=False)

                        form.instance.image_url = image_url

                    finally:
                        # CRITICAL-003: Ensure temp file is cleaned up
                        if temp_file_path and os.path.exists(temp_file_path):
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass

                except requests.RequestException as e:
                    form.add_error('image_url', f"Error al descargar la imagen: {str(e)}")
                    return self.form_invalid(form)
                except Exception as e:
                    form.add_error('image_url', f"Error al procesar la imagen: {str(e)}")
                    return self.form_invalid(form)

        try:
            messages.success(self.request, _("Producto actualizado exitosamente."))
            return super().form_valid(form)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al actualizar el producto. Por favor intente nuevamente."))
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        context['title'] = _("Editar Producto")
        return context

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'agents/product_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = self.get_object()
        self.agent = self.product.agent_config.agent
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            messages.success(self.request, _("Producto eliminado exitosamente."))
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            # LOW-001: Manejo de errores mejorado
            messages.error(self.request, _("Error al eliminar el producto. Por favor intente nuevamente."))
            return redirect(reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id}))

    def get_success_url(self):
        return reverse_lazy('agents:agent_configure', kwargs={'agent_id': self.agent.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.agent
        return context
