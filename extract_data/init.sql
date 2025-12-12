-- Crear la base de datos si no existe
DO
$$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'artistas') THEN
      CREATE DATABASE artistas;
   END IF;
END
$$;

\c artistas;
-- Crear el usuario "pera" con la contraseña "manzana"
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'naynay') THEN
    -- Password removed from repository. Set a secure password via environment
    -- or create the role manually. Placeholder used here.
    CREATE ROLE naynay WITH LOGIN ENCRYPTED PASSWORD '<REPLACE_WITH_SECURE_PASSWORD>';
  END IF;
END
$$;

-- Otorgar todos los permisos sobre la base de datos "artistas" al usuario "pera"
GRANT ALL PRIVILEGES ON DATABASE artistas TO naynay;
