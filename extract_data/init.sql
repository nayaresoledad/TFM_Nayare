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
    CREATE ROLE naynay WITH LOGIN ENCRYPTED PASSWORD '85428542';
  END IF;
END
$$;

-- Otorgar todos los permisos sobre la base de datos "artistas" al usuario "pera"
GRANT ALL PRIVILEGES ON DATABASE artistas TO naynay;
