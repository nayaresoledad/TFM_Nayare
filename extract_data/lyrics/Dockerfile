FROM python:3.9

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos del proyecto
COPY . /app
COPY wait-for-it.sh /usr/local/bin/wait-for-it


# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

CMD ["./wait-for-it.sh", "db:5432", "--timeout=400", "--", "python", "main.py"]