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

# Instalar django-extensions, werkzeug y pyOpenSSL para runserver_plus con SSL
RUN pip install django-extensions werkzeug pyOpenSSL

# Copiar aplicación (desde la raíz del repo)
COPY . .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Generar certificado SSL auto-firmado para desarrollo
RUN openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -nodes -subj "/C=CO/ST=Bogota/L=Bogota/O=IACOL/OU=Dev/CN=localhost" \
    && chmod 644 /tmp/cert.pem /tmp/key.pem

USER app

EXPOSE 8000 8443

CMD sh -c "python manage.py migrate && python manage.py compilemessages && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"