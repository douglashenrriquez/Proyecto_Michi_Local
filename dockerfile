# Imagen base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias necesarias para pymysql
RUN apt-get update && apt-get install -y \
    gcc python3-dev libssl-dev libffi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python que ya trae tu proyecto
RUN pip install --no-cache-dir \
    Django==4.2.* \
    pymysql \
    django-cors-headers \
    cryptography

# Copiar el código del proyecto
COPY . .

# Exponer puerto
EXPOSE 3000

# Ejecutar el servidor Django
CMD python manage.py runserver 0.0.0.0:3000

