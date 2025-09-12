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

    class Meta:
        unique_together = ['user', 'agent']

    def __str__(self):
        return f"Config: {self.user.username} - {self.agent.name}"

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
