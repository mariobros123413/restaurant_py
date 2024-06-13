# Utiliza una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos requirements.txt y diagramaBarra.py al directorio de trabajo
COPY requirements.txt .
COPY diagramaBarra.py .

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que la aplicación estará disponible
EXPOSE 8050

# Comando para ejecutar la aplicación
CMD ["python", "diagramaBarra.py"]
