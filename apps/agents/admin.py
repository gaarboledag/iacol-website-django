from django.contrib import admin
from .models import AgentCategory, Agent, UserSubscription, AgentConfiguration, AgentUsageLog

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

@admin.register(AgentUsageLog)
class AgentUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent', 'success', 'execution_time', 'created_at']
    list_filter = ['success', 'agent', 'created_at']
    search_fields = ['user__username', 'agent__name']
    readonly_fields = ['created_at']
