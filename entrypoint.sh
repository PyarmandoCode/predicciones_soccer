#!/bin/sh

echo "⏳ Esperando a que la base de datos esté lista..."

# Esperar hasta que PostgreSQL esté disponible
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "✅ Base de datos disponible. Ejecutando migraciones..."
python manage.py makemigrations predictor 
python manage.py migrate --noinput

echo "🧑‍💻 Creando superusuario automático (si no existe)..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superusuario '{username}' creado correctamente.")
else:
    print(f"⚠️ El superusuario '{username}' ya existe.")
EOF

echo "🚀 Iniciando servidor de Django..."
exec python manage.py runserver 0.0.0.0:8000
