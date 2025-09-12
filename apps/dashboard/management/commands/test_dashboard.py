from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
import logging
import traceback

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test the dashboard functionality and gather detailed error information'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting dashboard test...'))
        
        # Get the first superuser for testing
        User = get_user_model()
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No superuser found. Please create one first.'))
                return
                
            self.stdout.write(self.style.SUCCESS(f'Testing with user: {user.email}'))
            
            # Test database connection
            self.stdout.write('Testing database connection...')
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f'Database connection test: {result[0] == 1}'))
            
            # Test UserSubscription model
            from apps.agents.models import UserSubscription, Agent
            
            self.stdout.write('\nTesting UserSubscription model...')
            subscriptions = UserSubscription.objects.filter(user=user, status='active').select_related('agent')
            self.stdout.write(f'Found {subscriptions.count()} active subscriptions')
            
            for sub in subscriptions:
                self.stdout.write(f'  - Agent: {sub.agent.name} (ID: {sub.agent_id})')
            
            # Test AgentUsageLog
            from apps.agents.models import AgentUsageLog
            
            self.stdout.write('\nTesting AgentUsageLog...')
            logs = AgentUsageLog.objects.filter(user=user).order_by('-created_at')[:5]
            self.stdout.write(f'Found {logs.count()} recent logs')
            
            for log in logs:
                self.stdout.write(f'  - {log.created_at}: {log.get_action_display()}')
            
            # Test AgentConfiguration
            from apps.agents.models import AgentConfiguration
            
            self.stdout.write('\nTesting AgentConfiguration...')
            configs = AgentConfiguration.objects.filter(user=user)
            self.stdout.write(f'Found {configs.count()} configurations')
            
            for config in configs:
                self.stdout.write(f'  - Agent ID: {config.agent_id}, Has config: {bool(config.configuration_data)}')
            
            # Test dashboard view
            self.stdout.write('\nTesting dashboard view...')
            from django.test import RequestFactory
            from django.contrib.messages.storage.fallback import FallbackStorage
            from . import views
            
            factory = RequestFactory()
            request = factory.get('/dashboard/')
            request.user = user
            
            # Setup messages framework
            setattr(request, 'session', 'session')
            messages = FallbackStorage(request)
            setattr(request, '_messages', messages)
            
            # Call the view
            response = views.dashboard_home(request)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Dashboard view returned 200 OK'))
            else:
                self.stdout.write(self.style.ERROR(f'Dashboard view returned status code: {response.status_code}'))
            
            # Check for error messages
            storage = getattr(request, '_messages', [])
            for message in storage:
                self.stdout.write(self.style.ERROR(f'Message: {message}'))
            
            self.stdout.write(self.style.SUCCESS('\nDashboard test completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during dashboard test: {str(e)}'))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            
            # Log additional database information if available
            if hasattr(e, '__cause__') and hasattr(e.__cause__, 'pgcode'):
                self.stdout.write(self.style.ERROR(f'PostgreSQL Error Code: {e.__cause__.pgcode}'))
                self.stdout.write(self.style.ERROR(f'Error Message: {e.__cause__.pgerror}'))
                if hasattr(e.__cause__, 'query'):
                    self.stdout.write(self.style.ERROR(f'Query: {e.__cause__.query}'))
