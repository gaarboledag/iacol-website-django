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
    
    # URLs para la gestión de categorías de proveedores
    path('<int:agent_id>/provider-categories/', views.ProviderCategoryListView.as_view(), name='provider_category_list'),
    path('<int:agent_id>/provider-categories/add/', views.ProviderCategoryCreateView.as_view(), name='provider_category_add'),
    path('provider-categories/<int:pk>/edit/', views.ProviderCategoryUpdateView.as_view(), name='provider_category_edit'),
    path('provider-categories/<int:pk>/delete/', views.ProviderCategoryDeleteView.as_view(), name='provider_category_delete'),
    
    # URLs para la gestión de marcas
    path('<int:agent_id>/brands/', views.BrandListView.as_view(), name='brand_list'),
    path('<int:agent_id>/brands/add/', views.BrandCreateView.as_view(), name='brand_add'),
    path('brands/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_edit'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),

    # URLs para la gestión de categorías de productos
    path('<int:agent_id>/product-categories/', views.ProductCategoryListView.as_view(), name='product_category_list'),
    path('<int:agent_id>/product-categories/add/', views.ProductCategoryCreateView.as_view(), name='product_category_add'),
    path('product-categories/<int:pk>/edit/', views.ProductCategoryUpdateView.as_view(), name='product_category_edit'),
    path('product-categories/<int:pk>/delete/', views.ProductCategoryDeleteView.as_view(), name='product_category_delete'),

    # URLs para la gestión de marcas de productos
    path('<int:agent_id>/product-brands/', views.ProductBrandListView.as_view(), name='product_brand_list'),
    path('<int:agent_id>/product-brands/add/', views.ProductBrandCreateView.as_view(), name='product_brand_add'),
    path('product-brands/<int:pk>/edit/', views.ProductBrandUpdateView.as_view(), name='product_brand_edit'),
    path('product-brands/<int:pk>/delete/', views.ProductBrandDeleteView.as_view(), name='product_brand_delete'),

    # URLs para la gestión de productos
    path('<int:agent_id>/products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # URLs para la gestión de información del centro automotriz
    path('<int:agent_id>/automotive-info/create/', views.AutomotiveCenterInfoCreateView.as_view(), name='automotive_info_create'),
    path('automotive-info/<int:pk>/edit/', views.AutomotiveCenterInfoUpdateView.as_view(), name='automotive_info_update'),
]
