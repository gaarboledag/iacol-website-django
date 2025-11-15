from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
from datetime import datetime
from django_ratelimit.decorators import ratelimit

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='POST')
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
@ratelimit(key='user', rate='60/m', method='GET')
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

@csrf_exempt
@ratelimit(key='ip', rate='20/m', method='GET')
def serve_media(request, path):
    """CRITICAL-002: Sirve archivos de media de forma segura con validaciones estrictas"""
    
    # Logging para debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Intentando servir archivo: {path}")
    
    # CRITICAL-002: Validación estricta de parámetros
    if not path or not isinstance(path, str):
        logger.warning("Path inválido proporcionado")
        raise Http404("Archivo no encontrado")
    
    # CRITICAL-002: Normalizar y validar path para prevenir path traversal
    # Eliminar caracteres peligrosos y normalizar el path
    normalized_path = os.path.normpath(path).lstrip(os.sep)
    
    # Lista de extensiones permitidas (whitelist estricta)
    ALLOWED_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.webp',  # Imágenes
        '.pdf', '.txt', '.doc', '.docx',  # Documentos
        '.mp4', '.avi', '.mov', '.webm',  # Videos
        '.mp3', '.wav', '.ogg',  # Audio
        '.zip', '.rar', '.7z'  # Archivos comprimidos
    }
    
    # Validar que el archivo tiene una extensión permitida
    file_ext = os.path.splitext(normalized_path)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Extensión no permitida: {file_ext}")
        raise Http404("Tipo de archivo no permitido")
    
    # Validar que el path no contiene caracteres peligrosos
    dangerous_patterns = ['..', '//', '\\\\', ':', '*', '?', '"', '<', '>', '|']
    if any(pattern in normalized_path for pattern in dangerous_patterns):
        logger.warning(f"Path contiene caracteres peligrosos: {path}")
        raise Http404("Path inválido")
    
    # Construir el path completo de forma segura
    file_path = os.path.join(settings.MEDIA_ROOT, normalized_path)
    
    # CRITICAL-002: Validar que el archivo está dentro del MEDIA_ROOT (prevenir directory traversal)
    try:
        abs_media_root = os.path.abspath(settings.MEDIA_ROOT)
        abs_file_path = os.path.abspath(file_path)
        if not abs_file_path.startswith(abs_media_root):
            logger.warning(f"Intento de acceso fuera del directorio permitido: {file_path}")
            raise Http404("Archivo no encontrado")
    except (TypeError, ValueError) as e:
        logger.error(f"Error en validación de paths: {e}")
        raise Http404("Archivo no encontrado")
    
    logger.info(f"Path validado: {file_path}")
    logger.info(f"Archivo existe: {os.path.exists(file_path)}")
    
    # Verificar que el archivo existe y es accesible
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        logger.warning(f"Archivo no encontrado: {file_path}")
        raise Http404("Archivo no encontrado")
    
    # Determinar tipo MIME basado en extensión de forma segura
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.webm': 'video/webm',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
    }
    content_type = mime_types.get(file_ext, 'application/octet-stream')

    try:
        # CRITICAL-002: Usar FileSystemStorage de Django para mayor seguridad
        if default_storage.exists(normalized_path):
            file_obj = default_storage.open(normalized_path, 'rb')
            response = HttpResponse(file_obj.read(), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(normalized_path)}"'
            
            # Headers de seguridad adicionales
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['Content-Security-Policy'] = "default-src 'none'"
            
            file_obj.close()
            return response
        else:
            logger.warning(f"Archivo no encontrado en storage: {normalized_path}")
            raise Http404("Archivo no encontrado")
            
    except IOError as e:
        logger.error(f"Error al leer archivo {file_path}: {e}")
        raise Http404("Error al leer el archivo")
    except Exception as e:
        logger.error(f"Error inesperado al servir archivo {file_path}: {e}")
        raise Http404("Error interno del servidor")
