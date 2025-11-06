# Imagen base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc python3-dev libssl-dev libffi-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    Django==4.2.* \
    pymysql \
    django-cors-headers \
    cryptography

# Copiar el código del proyecto
COPY . .

# Exponer puerto
EXPOSE 3000

# Esperar MySQL, migrar y ejecutar el servidor
CMD python wait_for_db.py && python manage.py migrate && python manage.py runserver 0.0.0.0:3000
