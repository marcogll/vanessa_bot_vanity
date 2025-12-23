# Usar una imagen base de Python actualizada
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Cambiar al directorio donde está el código fuente
WORKDIR /app/app

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
