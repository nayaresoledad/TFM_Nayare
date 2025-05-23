FROM python:3.9

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos del proyecto
COPY . /app
COPY wait-for-it.sh /usr/local/bin/wait-for-it


# Instalamos las dependencias
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el script
CMD ["./wait-for-it.sh", "db:5432", "--timeout=60", "--", "python", "obtener_artistas.py"]