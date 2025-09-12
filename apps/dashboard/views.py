from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, DatabaseError
from django.core.exceptions import ObjectDoesNotExist
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
            
        # Obtener suscripciones activas del usuario con manejo de errores
        try:
            user_subscriptions = UserSubscription.objects.filter(
                user=request.user, 
                status='active'
            ).select_related('agent')
            logger.info(f"[DASHBOARD] Suscripciones encontradas: {user_subscriptions.count()}")
        except Exception as e:
            logger.error(f"[DASHBOARD] Error al obtener suscripciones: {str(e)}\n{traceback.format_exc()}")
            user_subscriptions = []
            
        # Obtener estadísticas generales con manejo de errores
        try:
            total_executions = AgentUsageLog.objects.filter(user=request.user).count()
            recent_logs = AgentUsageLog.objects.filter(
                user=request.user
            ).select_related('agent').order_by('-created_at')[:5]
            logger.info(f"[DASHBOARD] Total de ejecuciones: {total_executions}")
        except Exception as e:
            logger.error(f"[DASHBOARD] Error al obtener estadísticas: {str(e)}\n{traceback.format_exc()}")
            total_executions = 0
            recent_logs = []
            
        # Verificar si hay configuraciones para los agentes suscritos
        try:
            if user_subscriptions:
                agent_ids = [sub.agent_id for sub in user_subscriptions]
                existing_configs = AgentConfiguration.objects.filter(
                    user=request.user,
                    agent_id__in=agent_ids
                ).values_list('agent_id', flat=True)
                
                # Agregar flag para saber si cada agente tiene configuración
                for sub in user_subscriptions:
                    sub.has_config = sub.agent_id in existing_configs
        except Exception as e:
            logger.error(f"[DASHBOARD] Error al verificar configuraciones: {str(e)}\n{traceback.format_exc()}")
        
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
            logger.error(f"[DASHBOARD] Error al obtener detalles de la base de datos: {str(db_err)}")
            
        messages.error(
            request,
            'Error al conectar con la base de datos. Por favor, inténtalo de nuevo más tarde.'
        )
        return redirect('home')
        
    except Exception as e:
        # Cualquier otro error
        error_msg = f"[DASHBOARD] Error inesperado para el usuario {request.user.email}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        messages.error(
            request,
            'Ha ocurrido un error inesperado al cargar el dashboard. El equipo técnico ha sido notificado.'
        )
        return redirect('home')
