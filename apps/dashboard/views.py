from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.agents.models import UserSubscription, AgentUsageLog

@login_required
def dashboard_home(request):
    """Dashboard principal del usuario"""
    user_subscriptions = UserSubscription.objects.filter(
        user=request.user, 
        status='active'
    ).select_related('agent')
    
    # Estadísticas generales
    total_executions = AgentUsageLog.objects.filter(user=request.user).count()
    recent_logs = AgentUsageLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    return render(request, 'dashboard/home.html', {
        'subscriptions': user_subscriptions,
        'total_executions': total_executions,
        'recent_logs': recent_logs,
    })
