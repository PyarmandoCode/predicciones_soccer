# Usar una imagen base oficial de Python
FROM python:3.10

# Configurar el directorio de trabajo
WORKDIR /app

# Copiar solo requirements primero
COPY requirements.txt .

# Instalar pip y actualizar
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto 8000 para Django
EXPOSE 8000

# Comando para ejecutar el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
