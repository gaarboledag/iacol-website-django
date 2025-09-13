from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AgentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-robot')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Agent(models.Model):
    PRICING_TYPES = [
        ('monthly', 'Mensual'),
        ('usage', 'Por Uso'),
        ('enterprise', 'Empresarial'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(AgentCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPES, default='monthly')
    n8n_workflow_id = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    # New visibility controls
    show_in_agents = models.BooleanField(default=True, help_text='Si está activo, aparece en el listado de Agents.')
    show_in_solutions = models.BooleanField(default=True, help_text='Si está activo, aparece en el listado público de Solutions.')
    allowed_users = models.ManyToManyField(User, blank=True, related_name='allowed_agents', help_text='Usuarios que pueden acceder al agente aunque no sea público en Agents o Solutions.')
    features = models.JSONField(default=list)
    image = models.ImageField(upload_to='agents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'agent']

    def __str__(self):
        return f"{self.user.username} - {self.agent.name}"

class AgentConfiguration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    configuration_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Nuevo campo para indicar si este agente tiene habilitada la gestión de proveedores
    enable_providers = models.BooleanField(
        default=False,
        verbose_name='Habilitar gestión de proveedores',
        help_text='Permitir a los usuarios gestionar proveedores para este agente'
    )

    class Meta:
        unique_together = ['user', 'agent']
        verbose_name = 'Configuración de agente'
        verbose_name_plural = 'Configuraciones de agentes'

    def __str__(self):
        return f"Config: {self.user.username} - {self.agent.name}"

class ProviderCategory(models.Model):
    """Modelo para categorías de proveedores"""
    name = models.CharField(max_length=100, verbose_name='Nombre de la categoría')
    agent_config = models.ForeignKey(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='provider_categories',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de proveedor'
        verbose_name_plural = 'Categorías de proveedores'
        unique_together = ['name', 'agent_config']
        ordering = ['name']

    def __str__(self):
        return self.name

class Provider(models.Model):
    """Modelo para almacenar información de proveedores de un agente"""
    name = models.CharField(max_length=200, verbose_name='Nombre del proveedor')
    phone = models.CharField(max_length=20, verbose_name='Número de teléfono')
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    category = models.ForeignKey(
        ProviderCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers',
        verbose_name='Categoría'
    )
    agent_config = models.ForeignKey(
        AgentConfiguration, 
        on_delete=models.CASCADE,
        related_name='providers',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}"

class AgentUsageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    execution_id = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    execution_time = models.FloatField()  # En segundos
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.user.username} - {self.agent.name} [{self.created_at}]"
