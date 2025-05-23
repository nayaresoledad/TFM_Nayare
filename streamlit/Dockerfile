# Imagen base de Python
FROM python:3.10-slim

# Crear directorio para la app
WORKDIR /app

# Copiar archivos de la app
COPY ./app /app

# Copiar el requirements.txt
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para lanzar Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
