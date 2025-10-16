from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('log-execution/', views.log_agent_execution, name='log_execution'),
    path('agent-stats/<int:agent_id>/', views.get_agent_stats, name='agent_stats'),
    path('media/<path:path>/', views.serve_media, name='serve_media'),
]
