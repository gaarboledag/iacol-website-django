from django.contrib import admin
from django.utils.html import format_html
from .models import BlogPost, APIKey


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista
    list_display = ('title', 'category', 'is_published', 'published_date', 'get_short_excerpt')
    list_filter = ('is_published', 'category', 'published_date')
    search_fields = ('title', 'excerpt', 'content')
    ordering = ('-published_date',)

    # Campos de solo lectura
    readonly_fields = ('slug', 'published_date', 'updated_date')

    # Campos que se muestran en el formulario
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'slug', 'is_published', 'category')
        }),
        ('Contenido', {
            'fields': ('excerpt', 'hero_image'),
            'classes': ('collapse',)
        }),
        ('Secciones Estructuradas', {
            'fields': (
                'problem_section', 'problem_image',
                'why_automate_section',
                'sales_angle_section',
                'how_it_works_section',
                'agent_diagram_image',
                'benefits_section',
                'hypothetical_case_section',
                'case_image',
                'final_cta_section',
                'optional_icon_image'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('published_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )

    # Métodos personalizados
    def get_short_excerpt(self, obj):
        """Muestra un excerpt corto en la lista"""
        if obj.excerpt:
            return obj.excerpt[:50] + '...' if len(obj.excerpt) > 50 else obj.excerpt
        return '-'
    get_short_excerpt.short_description = 'Resumen'

    # Acciones personalizadas
    actions = ['publish_posts', 'unpublish_posts']

    def publish_posts(self, request, queryset):
        """Publica los posts seleccionados"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} posts publicados exitosamente.')
    publish_posts.short_description = 'Publicar posts seleccionados'

    def unpublish_posts(self, request, queryset):
        """Despublica los posts seleccionados"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} posts despublicados exitosamente.')
    unpublish_posts.short_description = 'Despublicar posts seleccionados'

    # Configuración de formulario
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Personalizar widgets si es necesario
        return form

    # Mostrar preview de imágenes en el admin
    def hero_image_preview(self, obj):
        if obj.hero_image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.hero_image.url)
        return '-'
    hero_image_preview.short_description = 'Vista previa Hero'

    # Añadir la preview a list_display si se quiere
    # list_display = ('title', 'hero_image_preview', 'is_published', 'published_date')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """
    Admin interface for API keys management.
    """
    list_display = ('name', 'key_preview', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'key', 'created_by__username')
    readonly_fields = ('key', 'created_at')

    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'created_by', 'is_active')
        }),
        ('Clave API', {
            'fields': ('key',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def key_preview(self, obj):
        """Show first 8 and last 4 characters of the API key"""
        if obj.key:
            return f"{obj.key[:8]}...{obj.key[-4:]}"
        return '-'
    key_preview.short_description = 'Clave API'

    def get_queryset(self, request):
        """Only show API keys created by the current user, unless superuser"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit created_by choices to current user for non-superusers"""
        if db_field.name == 'created_by' and not request.user.is_superuser:
            kwargs['initial'] = request.user.id
            kwargs['disabled'] = True
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
