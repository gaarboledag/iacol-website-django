#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iacol_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@iacol.online',
            password='admin123'
        )
        print("✅ Superuser 'admin' created successfully!")
        print("Username: admin")
        print("Email: admin@iacol.online")
        print("Password: admin123")
    else:
        print("⚠️  Superuser 'admin' already exists!")
except Exception as e:
    print(f"❌ Error creating superuser: {e}")