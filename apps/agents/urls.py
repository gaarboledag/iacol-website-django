from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('', views.agent_list, name='agent_list'),
    path('<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('<int:agent_id>/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('<int:agent_id>/configure/', views.agent_configure, name='agent_configure'),
]
