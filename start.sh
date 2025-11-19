#!/bin/bash
echo "=== Starting Application ==="

# Создаем базу и выполняем миграции
python manage.py migrate

# Создаем суперпользователя
python -c "
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('SUPERUSER CREATED: admin / admin123')
else:
    print('SUPERUSER EXISTS')
"

# Создаем тестовые товары
python -c "
import django
django.setup()
from items.models import Item
if not Item.objects.exists():
    Item.objects.create(name='Test Product', description='Test', price=1000, currency='usd')
    print('TEST ITEM CREATED')
else:
    print('ITEMS EXIST')
"

echo "=== Starting Server ==="
python manage.py runserver 0.0.0.0:8000