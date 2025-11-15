import os
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iacol_project.settings')

app = Celery('iacol')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.task
def send_email_task(subject, message, recipient_list):
    """Tarea asíncrona para envío de emails"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return f"Email sent successfully to {recipient_list}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@app.task
def heavy_processing_task(data):
    """Tarea de procesamiento pesado - ejemplo"""
    # Simular procesamiento pesado
    import time
    time.sleep(5)  # Simular trabajo intensivo

    # Procesar datos
    result = {
        'processed_items': len(data) if isinstance(data, list) else 1,
        'status': 'completed'
    }

    return result
