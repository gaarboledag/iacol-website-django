# Generated migration for JSONField GIN indexes

from django.db import migrations
from django.contrib.postgres.indexes import GinIndex

class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0011_add_provider_image_and_validators'),
    ]

    operations = [
        # MEDIUM-002: Add GIN indexes for JSONField queries
        migrations.AddIndex(
            model_name='agentconfiguration',
            index=GinIndex(
                name='agent_config_data_gin',
                fields=['configuration_data'],
                opclasses=['jsonb_path_ops']
            ),
        ),
        migrations.AddIndex(
            model_name='automotivecenterinfo',
            index=GinIndex(
                name='auto_center_hours_gin',
                fields=['business_hours'],
                opclasses=['jsonb_path_ops']
            ),
        ),
    ]