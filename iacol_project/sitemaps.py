from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.agents.models import Agent

class StaticSitemap(Sitemap):
    """Sitemap for static pages"""
    changefreq = 'monthly'
    priority = 0.8
    template_name = None

    def items(self):
        return [
            'home',
            'about',
            'contact',
            'solutions',
            'resources',
            'lucid_team',
            'findpartai_landing',
            'mechai_landing',
            'automotive',
            'custom_service',
            'masterclass_auto_ai',
            'dental_ai_landing',
            'ibague_ai_landing',
            'bogota_ai_landing',
            'cali_ai_landing',
            'medellin_ai_landing',
            'barranquilla_ai_landing',
            'cartagena_ai_landing',
        ]

    def location(self, item):
        return reverse(item)


class AgentSitemap(Sitemap):
    """Sitemap for public agents"""
    changefreq = 'weekly'
    priority = 0.6
    template_name = None

    def items(self):
        return Agent.objects.filter(is_active=True, show_in_solutions=True).select_related('category').order_by('id')

    def location(self, obj):
        return reverse('agents:agent_detail', args=[obj.pk])


class PaymentSitemap(Sitemap):
    """Sitemap for payment plans"""
    changefreq = 'monthly'
    priority = 0.5
    template_name = None

    def items(self):
        return ['payments:plans']

    def location(self, item):
        return reverse(item)