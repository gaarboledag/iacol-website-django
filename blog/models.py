from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid


class APIKey(models.Model):
    """
    API Key model for external service authentication (N8N, etc.)
    """
    name = models.CharField("Nombre", max_length=100, help_text="Nombre descriptivo para la clave API")
    key = models.CharField("Clave API", max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField("Creada", auto_now_add=True)
    is_active = models.BooleanField("Activa", default=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='api_keys')

    class Meta:
        verbose_name = "Clave API"
        verbose_name_plural = "Claves API"

    def save(self, *args, **kwargs):
        if not self.key:
            # Generate a secure random key
            self.key = uuid.uuid4().hex + uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Activa' if self.is_active else 'Inactiva'})"


class BlogPost(models.Model):
    # Basic fields
    title = models.CharField("Título (H1)", max_length=200)
    slug = models.SlugField("URL amigable", unique=True, blank=True)
    is_published = models.BooleanField("Publicado", default=False)
    published_date = models.DateTimeField("Fecha de publicación", auto_now_add=True)
    updated_date = models.DateTimeField("Última modificación", auto_now=True)

    # Structured content sections
    hero_image = models.ImageField("Imagen Hero", upload_to='blog/hero/', help_text="Imagen principal del post")

    problem_section = models.TextField("Problema", help_text="Descripción del problema que resuelve")
    problem_image = models.ImageField("Imagen Problema", upload_to='blog/problem/', blank=True, null=True)

    why_automate_section = models.TextField("Por qué automatizar", help_text="Explicación de por qué automatizar")
    sales_angle_section = models.TextField("Ángulo de venta", help_text="Punto de venta único")
    how_it_works_section = models.TextField("Cómo funciona", help_text="Explicación técnica del funcionamiento")

    agent_diagram_image = models.ImageField("Diagrama del Agente", upload_to='blog/diagram/', help_text="Imagen del diagrama del agente")

    benefits_section = models.TextField("Beneficios", help_text="Lista o descripción de beneficios")
    hypothetical_case_section = models.TextField("Caso hipotético", help_text="Ejemplo hipotético de uso")

    case_image = models.ImageField("Imagen Caso/Historia", upload_to='blog/case/', blank=True, null=True)

    final_cta_section = models.TextField("CTA Final", help_text="Llamado a la acción final")
    optional_icon_image = models.ImageField("Imagen Icono (opcional)", upload_to='blog/icon/', blank=True, null=True)

    # Metadata
    excerpt = models.TextField("Resumen breve", max_length=300, help_text="Para mostrar en listados y SEO")
    meta_description = models.CharField("Meta descripción", max_length=160, blank=True)
    category = models.CharField("Categoría", max_length=20, choices=[
        ('guias', 'Guías y buenas prácticas'),
        ('casos', 'Casos de uso'),
        ('faq', 'Preguntas frecuentes'),
    ], default='guias')

    class Meta:
        ordering = ['-published_date']
        verbose_name = "Entrada del Blog"
        verbose_name_plural = "Entradas del Blog"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:blog_detail', kwargs={'slug': self.slug})
