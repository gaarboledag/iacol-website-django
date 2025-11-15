# Generated manually for audit fixes

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0010_product_image_upload_method_product_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='providers/', verbose_name='Imagen del proveedor'),
        ),
        migrations.AlterField(
            model_name='agent',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name='Precio'),
        ),
        migrations.AlterField(
            model_name='provider',
            name='phone',
            field=models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(message='El número de teléfono debe tener el formato: \'+999999999\'. Hasta 15 dígitos permitidos.', regex='^\\+?1?\\d{9,15}$')], verbose_name='Número de teléfono'),
        ),
        migrations.AddIndex(
            model_name='agentconfiguration',
            index=models.Index(fields=['user', 'agent'], name='agents_agen_user_age_12345_idx'),
        ),
        migrations.AddIndex(
            model_name='brand',
            index=models.Index(fields=['agent_config'], name='agents_brand_agent_co_12345_idx'),
        ),
        migrations.AddIndex(
            model_name='productbrand',
            index=models.Index(fields=['agent_config'], name='agents_prod_agent_co_12345_idx'),
        ),
        migrations.AddIndex(
            model_name='productcategory',
            index=models.Index(fields=['agent_config'], name='agents_prod_agent_co_67890_idx'),
        ),
        migrations.AddIndex(
            model_name='provider',
            index=models.Index(fields=['agent_config', 'name'], name='agents_prov_agent_co_12345_idx'),
        ),
        migrations.AddIndex(
            model_name='provider',
            index=models.Index(fields=['agent_config', 'city'], name='agents_prov_agent_co_67890_idx'),
        ),
        migrations.AddIndex(
            model_name='provider',
            index=models.Index(fields=['category'], name='agents_provider_category_id_idx'),
        ),
        migrations.AddIndex(
            model_name='providercategory',
            index=models.Index(fields=['agent_config'], name='agents_prov_agent_co_99999_idx'),
        ),
        migrations.AddIndex(
            model_name='agentusagelog',
            index=models.Index(fields=['execution_time'], name='agents_agent_execution_12345_idx'),
        ),
    ]