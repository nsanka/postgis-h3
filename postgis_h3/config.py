import os
from enum import Enum
import logging
from dotenv import load_dotenv
from pyspark.sql import SparkSession

class DatabaseSaveModes(str, Enum):
   """Supportable modes for saving database tables."""

   APPEND = 'append'
   OVERWRITE = 'overwrite'
   READONLY = 'readonly'

def load_dotenv_file():
   load_dotenv()
   env = {
      "driver": os.environ.get("PG_DRIVER"),
      "host": os.environ.get("PG_HOST"),
      "port": os.environ.get("PG_PORT"),
      "database": os.environ.get("PG_DBNAME"),
      "username": os.environ.get("PG_USERNAME"),
      "password": os.environ.get("PG_PASSWORD"),
      "pg_jars_path": os.environ.get("PG_JARS_PATH")
   }
   return env

def get_config_pyspark():
   env = load_dotenv_file()
   config = {
      "url": f"jdbc:{env['driver']}://{env['host']}:{env['port']}/{env['database']}",
      "pg_jars_path": env['pg_jars_path'],
      "properties": {
         "user": env['username'],
         "password": env['password'],
         "driver": "org.postgresql.Driver"
      }
   }
   return config

def get_spark_session():
   """Create SparkSession and return it.
   Args:
      postgesql_jars_path (str): Path to the PostgreSQL JAR file
   Returns:
      spark (SparkSession): The Spark session
   """
   config_pyspark = get_config_pyspark()
   spark = SparkSession.builder \
      .config("spark.jars", config_pyspark['pg_jars_path']) \
      .master("local[*]").appName("PySpark_PostGIS").getOrCreate()
   return spark

def read_data_from_postgis_db(spark, table_name, logger=None):
   """Get the OSM data from the PostGIS database.
   Args:
      table_name (str): The name of the table in the database
      state (str): The state to filter the data
   Returns:
      data (DataFrame): The parking data for the state
   """
   sql_query = f"SELECT * FROM {table_name}"
   if logger: logger.info(f"Reading data from {table_name}")
   try:
      config_pyspark = get_config_pyspark()
      data = spark.read.format("jdbc") \
         .option("driver", config_pyspark['properties']['driver']) \
         .option("url", config_pyspark['url']) \
         .option("query", sql_query) \
         .option("user", config_pyspark['properties']['user']) \
         .option("password", config_pyspark['properties']['password']) \
         .load()
   except Exception as e:
      if logger: logger.error(f"Error reading data from {table_name}: {e}")
      raise Exception(f"Error reading data from {table_name}: {e}")
   return data

def write_data_to_postgis_db(table_name, data, mode=DatabaseSaveModes.OVERWRITE, logger=None):
   """Write the OSM data to the PostGIS database.
   Args:
      table_name (str): The name of the table in the database
      state (str): The state to filter the data
      data (DataFrame): The parking data for the state
   """
   if logger: logger.info(f"Writing data to {table_name}")
   try:
      config_pyspark = get_config_pyspark()
      data.write.format("jdbc") \
         .option("driver", config_pyspark['properties']['driver']) \
         .option("url", config_pyspark['url']) \
         .option("dbtable", table_name) \
         .option("user", config_pyspark['properties']['user']) \
         .option("password", config_pyspark['properties']['password']) \
         .mode(mode.value) \
         .save()
   except Exception as e:
      if logger: logger.error(f"Error writing data to {table_name}: {e}")
      raise Exception(f"Error writing data to {table_name}: {e}")

if __name__ == "__main__":
   logger = logging.getLogger(__name__)
   logging.basicConfig(filename='h3_indices.log', level=logging.INFO)
   logger.info('Started processing H3 data.')

   spark = get_spark_session()
