from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator, EmailValidator
import os
import uuid

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
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
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

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'show_in_agents']),
            models.Index(fields=['is_active', 'show_in_solutions']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def get_image_url(self):
        """Devuelve la URL correcta para acceder a la imagen"""
        if self.image and self.image.name:
            return f"/api/media/agents/{self.image.name}/"
        return None

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
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['status', 'end_date']),
        ]

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

    # Nuevo campo para indicar si este agente tiene habilitada la gestión de productos
    enable_products = models.BooleanField(
        default=False,
        verbose_name='Habilitar gestión de productos',
        help_text='Permitir a los usuarios gestionar productos para este agente'
    )

    # Nuevo campo para indicar si este agente tiene habilitada la información del centro automotriz
    enable_automotive_info = models.BooleanField(
        default=False,
        verbose_name='Habilitar información del centro automotriz',
        help_text='Permitir a los usuarios configurar información del centro automotriz para este agente'
    )

    class Meta:
        unique_together = ['user', 'agent']
        verbose_name = 'Configuración de agente'
        verbose_name_plural = 'Configuraciones de agentes'
        indexes = [
            models.Index(fields=['user', 'agent']),
        ]

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
        indexes = [
            models.Index(fields=['agent_config']),
        ]

    def __str__(self):
        return self.name

class Brand(models.Model):
    """Modelo para almacenar marcas de proveedores"""
    name = models.CharField(max_length=100, verbose_name='Nombre de la marca')
    agent_config = models.ForeignKey(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='brands',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        unique_together = ['name', 'agent_config']
        ordering = ['name']
        indexes = [
            models.Index(fields=['agent_config']),
        ]

    def __str__(self):
        return self.name

class Provider(models.Model):
    """Modelo para almacenar información de proveedores de un agente"""
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe tener el formato: '+999999999'. Hasta 15 dígitos permitidos."
    )

    name = models.CharField(max_length=200, verbose_name='Nombre del proveedor')
    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name='Número de teléfono'
    )
    city = models.CharField(max_length=100, verbose_name='Ciudad')
    image = models.ImageField(upload_to='providers/', null=True, blank=True, verbose_name='Imagen del proveedor')
    category = models.ForeignKey(
        ProviderCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers',
        verbose_name='Categoría'
    )
    brands = models.ManyToManyField(
        Brand,
        related_name='providers',
        blank=True,
        verbose_name='Marcas que maneja'
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
        indexes = [
            models.Index(fields=['agent_config', 'name']),
            models.Index(fields=['agent_config', 'city']),
            models.Index(fields=['category']),
        ]

    def get_image_url(self):
        """Devuelve la URL correcta para acceder a la imagen"""
        if self.image and self.image.name:
            return f"/api/media/{self.image.name}/"
        return None

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}"

class ProductCategory(models.Model):
    """Modelo para categorías de productos"""
    name = models.CharField(max_length=100, verbose_name='Nombre de la categoría')
    agent_config = models.ForeignKey(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='product_categories',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría de producto'
        verbose_name_plural = 'Categorías de productos'
        unique_together = ['name', 'agent_config']
        ordering = ['name']
        indexes = [
            models.Index(fields=['agent_config']),
        ]

    def __str__(self):
        return self.name

class ProductBrand(models.Model):
    """Modelo para almacenar marcas de productos"""
    name = models.CharField(max_length=100, verbose_name='Nombre de la marca')
    agent_config = models.ForeignKey(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='product_brands',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Marca de producto'
        verbose_name_plural = 'Marcas de productos'
        unique_together = ['name', 'agent_config']
        ordering = ['name']
        indexes = [
            models.Index(fields=['agent_config']),
        ]

    def __str__(self):
        return self.name

class Product(models.Model):
    """Modelo para almacenar productos de un agente"""
    UPLOAD_METHODS = [
        ('file', 'Subir archivo'),
        ('url', 'Desde URL'),
    ]

    title = models.CharField(max_length=200, verbose_name='Título del producto')
    description = models.TextField(verbose_name='Descripción')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Precio'
    )
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Imagen del producto')
    image_upload_method = models.CharField(
        max_length=10,
        choices=UPLOAD_METHODS,
        default='file',
        verbose_name='Método de carga de imagen'
    )
    image_url = models.URLField(null=True, blank=True, verbose_name='URL de la imagen')

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Categoría'
    )
    brand = models.ForeignKey(
        ProductBrand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Marca'
    )
    agent_config = models.ForeignKey(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Configuración del agente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def get_image_url(self):
        """Devuelve la URL correcta para acceder a la imagen"""
        if self.image and self.image.name:
            return f"/api/media/{self.image.name}/"
        return None

    def __str__(self):
        return f"{self.title} - ${self.price}"

class AutomotiveCenterInfo(models.Model):
    """Modelo para almacenar información del centro automotriz para agentes MechAI"""
    agent_config = models.OneToOneField(
        AgentConfiguration,
        on_delete=models.CASCADE,
        related_name='automotive_center_info',
        verbose_name='Configuración del agente'
    )
    physical_address = models.TextField(verbose_name='Dirección física del taller')
    business_hours = models.JSONField(
        default=dict,
        verbose_name='Horarios de atención',
        help_text='Horarios de atención en formato JSON'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Información del Centro Automotriz'
        verbose_name_plural = 'Información de Centros Automotrices'

    def __str__(self):
        return f"Centro Automotriz: {self.agent_config.agent.name}"

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

    class Meta:
        # Consider partitioning by created_at for large datasets
        # db_table = 'agents_agentusagelog'  # For partitioning in PostgreSQL
        indexes = [
            models.Index(fields=['user', 'agent', 'created_at']),
            models.Index(fields=['agent', 'created_at']),
            models.Index(fields=['success', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['execution_time']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.user.username} - {self.agent.name} [{self.created_at}]"
