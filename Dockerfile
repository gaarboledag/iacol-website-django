FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    gettext \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements (desde la raíz del repo)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# LOW-002: Solo instalar dependencias de desarrollo en desarrollo, no en producción
# Las siguientes líneas se mueven a un requirements-dev.txt o se instalan condicionalmente
# RUN pip install django-extensions werkzeug pyOpenSSL

# Copiar aplicación (desde la raíz del repo)
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Crear directorios necesarios y dar permisos
RUN mkdir -p /app/staticfiles_collected /app/media \
    && chown -R app:app /app/staticfiles_collected /app/media

# NO generar certificado SSL en producción - esto debe hacerse en desarrollo
# Las siguientes líneas se comentan para producción
# RUN openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -nodes -subj "/C=CO/ST=Bogota/L=Bogota/O=IACOL/OU=Dev/CN=localhost" \
#     && chmod 644 /tmp/cert.pem /tmp/key.pem

USER app

EXPOSE 8000 8443

# Use Gunicorn with UvicornWorker for ASGI support in production
CMD sh -c "python manage.py migrate && python manage.py compilemessages && python manage.py collectstatic --noinput && gunicorn iacol_project.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"