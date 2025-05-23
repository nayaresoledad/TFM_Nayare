#!/bin/bash

# Cargar variables de entorno desde .env
set -o allexport
source .env
set +o allexport

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backups"
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Crear carpeta de backups si no existe
mkdir -p "$BACKUP_DIR"

echo "📦 Creando copia de seguridad comprimida en $BACKUP_FILE..."

# Ejecutar backup desde Docker con compresión gzip
docker exec -i tfm_canciones_db_1 pg_dump -U "$POSTGRES_USER" -d artistas | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Copia de seguridad completada exitosamente."
else
  echo "❌ Error durante la copia de seguridad." >&2
fi
