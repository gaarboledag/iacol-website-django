from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
import logging
import traceback

from apps.agents.models import UserSubscription, AgentUsageLog, Agent, AgentConfiguration

logger = logging.getLogger(__name__)

@login_required
def dashboard_home(request):
    """Dashboard principal del usuario"""
    try:
        logger.info(f"[DASHBOARD] Iniciando dashboard para usuario: {request.user.email}")
        
        # Verificar si el usuario está autenticado correctamente
        if not request.user.is_authenticated:
            logger.error("[DASHBOARD] Usuario no autenticado")
            messages.error(request, 'Debes iniciar sesión para acceder al dashboard.')
            return redirect('account_login')
            
        # CRITICAL-001: Optimización - Una sola consulta con select_related y annotate
        try:
            # Query optimizada que combina todas las estadísticas en una sola consulta
            dashboard_data = UserSubscription.objects.filter(
                user=request.user,
                status='active',
                agent__is_active=True
            ).select_related('agent').prefetch_related('agent__agentusagelog')
            
            user_subscriptions = list(dashboard_data)
            logger.info(f"[DASHBOARD] Suscripciones encontradas: {len(user_subscriptions)}")
            
            # Obtener configuraciones de una sola vez
            if user_subscriptions:
                agent_ids = [sub.agent_id for sub in user_subscriptions]
                existing_configs = set(AgentConfiguration.objects.filter(
                    user=request.user,
                    agent_id__in=agent_ids
                ).values_list('agent_id', flat=True))
                
                # Agregar flag de configuración
                for sub in user_subscriptions:
                    sub.has_config = sub.agent_id in existing_configs
            else:
                existing_configs = set()
                
        except Exception as e:
            logger.error(f"[DASHBOARD] Error al obtener suscripciones: {str(e)}\n{traceback.format_exc()}")
            user_subscriptions = []
            existing_configs = set()
            
        # CRITICAL-001: Optimización - Obtener logs recientes con select_related
        try:
            recent_logs = AgentUsageLog.objects.filter(
                user=request.user
            ).select_related('agent').order_by('-created_at')[:5]
            total_executions = AgentUsageLog.objects.filter(user=request.user).count()
            logger.info(f"[DASHBOARD] Total de ejecuciones: {total_executions}")
        except Exception as e:
            logger.error(f"[DASHBOARD] Error al obtener estadísticas: {str(e)}\n{traceback.format_exc()}")
            total_executions = 0
            recent_logs = []
        
        # Preparar el contexto
        context = {
            'subscriptions': user_subscriptions,
            'total_executions': total_executions,
            'recent_logs': recent_logs,
        }
        
        logger.info("[DASHBOARD] Renderizando plantilla dashboard")
        return render(request, 'dashboard/home.html', context)
        
    except DatabaseError as e:
        # Error específico de base de datos
        error_msg = f"[DASHBOARD] Error de base de datos: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        # Intentar obtener más detalles del error
        try:
            if hasattr(e, '__cause__') and hasattr(e.__cause__, 'pgcode'):
                logger.error(f"[DASHBOARD] Código de error PostgreSQL: {e.__cause__.pgcode}")
                logger.error(f"[DASHBOARD] Mensaje de error: {e.__cause__.pgerror}")
                logger.error(f"[DASHBOARD] Consulta SQL: {getattr(e.__cause__, 'query', 'No disponible')}")
        except Exception as db_err:
            logger.error(f"[DASHBOARD] Error al obtener detalles de la base de datos: {db_err}")
            
        messages.error(
            request,
            'Error al conectar con la base de datos. Por favor, inténtalo de nuevo más tarde.'
        )
        return redirect('home')
        
    except Exception as e:
        # LOW-001: Manejo consistente de errores
        error_msg = f"[DASHBOARD] Error inesperado para el usuario {request.user.email}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        messages.error(
            request,
            'Ha ocurrido un error inesperado al cargar el dashboard. El equipo técnico ha sido notificado.'
        )
        return redirect('home')
