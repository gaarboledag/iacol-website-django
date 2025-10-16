from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.conf import settings
from apps.agents.models import Agent, AgentUsageLog
import json
import os
from datetime import datetime

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_agent_execution(request):
    """Registra la ejecución de un agente desde N8N"""
    try:
        data = request.data
        user_id = data.get('user_id')
        agent_id = data.get('agent_id')
        execution_id = data.get('execution_id')
        input_data = data.get('input_data', {})
        output_data = data.get('output_data', {})
        execution_time = data.get('execution_time', 0)
        success = data.get('success', True)
        error_message = data.get('error_message', '')
        
        user = User.objects.get(id=user_id)
        agent = Agent.objects.get(id=agent_id)
        
        usage_log = AgentUsageLog.objects.create(
            user=user,
            agent=agent,
            execution_id=execution_id,
            input_data=input_data,
            output_data=output_data,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        
        return Response({
            'status': 'success',
            'log_id': usage_log.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agent_stats(request, agent_id):
    """Obtiene estadísticas de un agente para un usuario"""
    try:
        agent = Agent.objects.get(id=agent_id)
        logs = AgentUsageLog.objects.filter(user=request.user, agent=agent)
        
        total = logs.count()
        successful = logs.filter(success=True).count()
        failed = logs.filter(success=False).count()
        
        return Response({
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        })
        
    except Agent.DoesNotExist:
        return Response({
            'error': 'Agent not found'
        }, status=status.HTTP_404_NOT_FOUND)


@permission_classes([])
def serve_media(request, path):
    """Sirve archivos de media de forma segura con logging para debugging"""
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    # Logging para debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Intentando servir archivo: {file_path}")
    logger.info(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    logger.info(f"Path solicitado: {path}")
    logger.info(f"Archivo existe: {os.path.exists(file_path)}")
    logger.info(f"Es archivo: {os.path.isfile(file_path) if os.path.exists(file_path) else 'N/A'}")

    if os.path.exists(file_path) and os.path.isfile(file_path):
        # Determinar tipo MIME basado en extensión
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        content_type = mime_types.get(ext, 'application/octet-stream')

        try:
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
                return response
        except IOError as e:
            logger.error(f"Error al leer archivo {file_path}: {e}")
            raise Http404("Error al leer el archivo")
    logger.warning(f"Archivo no encontrado: {file_path}")
    raise Http404("Archivo no encontrado")
