from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'agents'

urlpatterns = [
    # URLs existentes
    path('', views.agent_list, name='agent_list'),
    path('<int:agent_id>/', views.agent_detail, name='agent_detail'),
    # Redirigir dashboard a configure
    path('<int:agent_id>/dashboard/', RedirectView.as_view(pattern_name='agents:agent_configure', permanent=False)),
    path('<int:agent_id>/configure/', views.agent_configure, name='agent_configure'),
    
    # URLs para la gestión de módulos
    path('<int:agent_id>/modules/<str:module_name>/toggle/', views.toggle_module, name='toggle_module'),
    
    # URLs para la gestión de proveedores
    path('<int:agent_id>/providers/add/', views.ProviderCreateView.as_view(), name='provider_add'),
    path('providers/<int:pk>/edit/', views.ProviderUpdateView.as_view(), name='provider_edit'),
    path('providers/<int:pk>/delete/', views.ProviderDeleteView.as_view(), name='provider_delete'),
    
    # Otras URLs existentes...
]
