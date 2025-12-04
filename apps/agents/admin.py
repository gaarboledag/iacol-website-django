from django.contrib import admin
from .models import AgentCategory, Agent, UserSubscription, AgentConfiguration, AgentUsageLog, Product, AutomotiveCenterInfo, AdvancedCatalogCategory, AdvancedCatalogProduct, AdvancedCatalogModel, AdvancedCatalogImage

@admin.register(AgentCategory)
class AgentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'pricing_type', 'is_active', 'show_in_agents', 'show_in_solutions', 'created_at']
    list_filter = ['category', 'pricing_type', 'is_active', 'show_in_agents', 'show_in_solutions']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'price', 'show_in_agents', 'show_in_solutions']
    filter_horizontal = ['allowed_users']
    fieldsets = (
        ('Información básica', {
            'fields': ('name', 'description', 'category', 'image')
        }),
        ('Comercial', {
            'fields': ('price', 'pricing_type')
        }),
        ('Operación', {
            'fields': ('n8n_workflow_id', 'is_active')
        }),
        ('Visibilidad y Acceso', {
            'fields': ('show_in_agents', 'show_in_solutions', 'allowed_users')
        }),
        ('Extras', {
            'fields': ('features',)
        }),
    )

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'agent']
    search_fields = ['user__username', 'agent__name']
    list_editable = ['status']

@admin.register(AgentConfiguration)
class AgentConfigurationAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent', 'updated_at']
    search_fields = ['user__username', 'agent__name']
    fieldsets = (
        (None, {
            'fields': ('user', 'agent')
        }),
        ('Configuración', {
            'fields': ('configuration_data', 'enable_providers', 'enable_products', 'enable_automotive_info', 'enable_advanced_catalog')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj and 'MechAI' not in obj.agent.name and 'FindPart' not in obj.agent.name:
            readonly = list(readonly) + ['enable_providers', 'enable_products', 'enable_automotive_info', 'enable_advanced_catalog']
        return readonly

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj)
        if obj and 'MechAI' not in obj.agent.name and 'FindPart' not in obj.agent.name:
            exclude = list(exclude or []) + ['enable_providers', 'enable_products', 'enable_automotive_info', 'enable_advanced_catalog']
        return exclude

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and 'MechAI' not in obj.agent.name and 'FindPart' not in obj.agent.name:
            if 'enable_providers' in form.base_fields:
                form.base_fields['enable_providers'].help_text = "Solo disponible para agentes MechAI y FindPartAI"
            if 'enable_products' in form.base_fields:
                form.base_fields['enable_products'].help_text = "Solo disponible para agentes MechAI"
            if 'enable_automotive_info' in form.base_fields:
                form.base_fields['enable_automotive_info'].help_text = "Solo disponible para agentes MechAI"
            if 'enable_advanced_catalog' in form.base_fields:
                form.base_fields['enable_advanced_catalog'].help_text = "Solo disponible para agentes MechAI"
        return form

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'agent_config', 'created_at']
    list_filter = ['agent_config__agent', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AutomotiveCenterInfo)
class AutomotiveCenterInfoAdmin(admin.ModelAdmin):
    list_display = ['agent_config', 'physical_address', 'updated_at']
    search_fields = ['agent_config__agent__name', 'physical_address']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AgentUsageLog)
class AgentUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent', 'success', 'execution_time', 'created_at']
    list_filter = ['success', 'agent', 'created_at']
    search_fields = ['user__username', 'agent__name']
    readonly_fields = ['created_at']

@admin.register(AdvancedCatalogCategory)
class AdvancedCatalogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'agent_config', 'created_at']
    list_filter = ['agent_config__agent', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AdvancedCatalogProduct)
class AdvancedCatalogProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'agent_config', 'created_at']
    list_filter = ['agent_config__agent', 'category', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AdvancedCatalogModel)
class AdvancedCatalogModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'price', 'created_at']
    list_filter = ['product__agent_config__agent', 'created_at']
    search_fields = ['name', 'product__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AdvancedCatalogImage)
class AdvancedCatalogImageAdmin(admin.ModelAdmin):
    list_display = ['model', 'image_type', 'created_at']
    list_filter = ['image_type', 'model__product__agent_config__agent', 'created_at']
    search_fields = ['model__name', 'model__product__name']
    readonly_fields = ['created_at']
