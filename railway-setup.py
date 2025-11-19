import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stripe_project.settings')
django.setup()

from django.core.management import execute_from_command_line

execute_from_command_line(['manage.py', 'migrate'])

from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Admin user created")
    
User.objects.create_superuser('admin', 'test@example.com', 'admin123')

from Items.models import Item
if not Item.objects.exists():
    Item.objects.create(name="Test Product", description="Test", price=1000, currency='usd')
    print("✅ Test item created")

print("🚀 Setup completed!")