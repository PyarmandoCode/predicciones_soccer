# Imagen base oficial de Python
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Dar permisos al script
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Usar el script como punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
