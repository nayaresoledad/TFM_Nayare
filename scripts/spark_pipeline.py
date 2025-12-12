"""
Ejemplo de pipeline PySpark para procesar letras y vectores distribuidos.
Adaptar rutas, credenciales y modelos antes de ejecutar.

Uso:
  spark-submit --master spark://<master>:7077 scripts/spark_pipeline.py
"""
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType, FloatType
from sentence_transformers import SentenceTransformer
import os
import logging

# Inicializar Spark
spark = SparkSession.builder \
    .appName("TFM_Music_Similarity") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
logger = logging.getLogger('spark_pipeline')

# Ejemplo: cargar datos desde PostgreSQL (configurar URL y credenciales)
JDBC_URL = os.getenv('JDBC_URL', 'jdbc:postgresql://localhost:5432/artistas')
JDBC_USER = os.getenv('POSTGRES_USER', 'postgres')
JDBC_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

songs_df = spark.read.format("jdbc") \
    .option("url", JDBC_URL) \
    .option("dbtable", "canciones") \
    .option("user", JDBC_USER) \
    .option("password", JDBC_PASSWORD) \
    .option("fetchsize", "1000") \
    .load()

logger.info(f"Songs loaded: {songs_df.count()}")

# Vectorización distribuida de textos usando Pandas UDF
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import ArrayType, FloatType
import pandas as pd

@pandas_udf(ArrayType(FloatType()))
def embed_text(texts: pd.Series) -> pd.Series:
    model = SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-small'))
    embeddings = model.encode(texts.tolist(), normalize_embeddings=True)
    return pd.Series([list(map(float, vec)) for vec in embeddings])

# Ejemplo: suponiendo que existe una columna 'letra' en songs_df
if 'letra' in songs_df.columns:
    vectors_df = songs_df.withColumn('lyrics_vector', embed_text(F.col('letra'))).select('id', 'artist_id', 'title', 'lyrics_vector')
    vectors_df.show(5)
    vectors_df.write.mode('overwrite').parquet('/data/tfm/lyrics_vectors/')
else:
    logger.warn('La columna "letra" no existe en la tabla canciones. Ajusta el pipeline.')

spark.stop()
