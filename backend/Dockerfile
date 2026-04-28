# backend/Dockerfile
FROM python:3.11-slim

# Variables de entorno para que Python no genere archivos .pyc y la salida por consola sea directa
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema:
#   - default-libmysqlclient-dev + pkg-config → mysqlclient
#   - libssl-dev + libffi-dev               → cryptography (AFIP certs)
#   - libxml2-dev + libxslt1-dev            → lxml (zeep SOAP parser)
#   - build-essential                        → compilador C para todos los anteriores
RUN apt-get update \
    && apt-get install -y \
        default-libmysqlclient-dev \
        build-essential \
        pkg-config \
        libssl-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
# Se copia solo requirements.txt primero para aprovechar la caché de Docker:
# si el código cambia pero requirements.txt no, este paso NO se re-ejecuta.
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

EXPOSE 8000