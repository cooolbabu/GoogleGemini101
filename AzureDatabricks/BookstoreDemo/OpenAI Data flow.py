# Databricks notebook source
# MAGIC %md
# MAGIC ### Get External Locations for DB-Demo

# COMMAND ----------

# DBTITLE 1,Get External Locations for DB_Demo
db_demo_location = spark.sql("describe external location `db_demo`").select("url").collect()[0][0]
checkpoint = f"{db_demo_location}checkpoint/"
landing = f"{db_demo_location}landing/"
bronze = f"{db_demo_location}bronze/"
silver = f"{db_demo_location}silver/"
gold = f"{db_demo_location}gold/"


print(f"Displaying External locations for DB-Demo: ")
print(f" Landing: {landing}\n Checkpoint: {checkpoint}\n Bronze: {bronze}\n Silver: {silver}\n Gold: {gold}\n")


# COMMAND ----------

# Select count of rows from raw_traffic and raw_roads
count_bronze_traffic = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.bronze.raw_traffic").collect()[0][0]
count_bronze_roads = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.bronze.raw_roads").collect()[0][0]
count_silver_traffic = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.silver.silver_traffic").collect()[0][0]
count_silver_roads = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.silver.silver_roads").collect()[0][0]
count_gold_traffic = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.gold.gold_traffic").collect()[0][0]
count_gold_roads = spark.sql("SELECT COUNT(*) FROM db_demo_catalog.gold.gold_roads").collect()[0][0]

print(f"Table row counts before the start of ELT workflow")
print(f"Row count of db_demo_catalog.bronze.raw_traffic: {count_bronze_traffic} and db_demo_catalog.bronze.raw_roads: {count_bronze_roads}")
print(f"Row count of db_demo_catalog.silver.silver_traffic: {count_silver_traffic} and db_demo_catalog.silver.silver_roads: {count_silver_roads}")
print(f"Row count of db_demo_catalog.gold.gold_traffic: {count_gold_traffic} and db_demo_catalog.gold.gold_roads: {count_gold_roads}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Read data from a CSV file

# COMMAND ----------

csv_file = "landing/raw_roads/raw_roads1.csv"
# Full path to the CSV file
csv_file_path = f"{db_demo_location}/{csv_file}"

# Read the CSV file into a DataFrame
df_raw_roads = spark.read.format("csv").option("header", "true").load(csv_file_path)

# Show the first few rows of the DataFrame
display(df_raw_roads)

# COMMAND ----------

# Replace spaces in column names
df_raw_roads = df_raw_roads.toDF(*[col.replace(' ', '_') for col in df_raw_roads.columns])

# Register the DataFrame as a temporary view
df_raw_roads.createOrReplaceTempView("tempView_raw_roads")

# Create the table using Spark SQL
spark.sql("""
CREATE TABLE IF NOT EXISTS db_demo_catalog.default.temp_raw_roads
USING DELTA
AS SELECT * FROM tempView_raw_roads
""")

# COMMAND ----------

spark.sql("SELECT COUNT(*) FROM db_demo_catalog.default.temp_raw_roads").collect()[0][0]

# COMMAND ----------

# Replace <cloud_storage_path> with the path to your CSV files in cloud storage
cloud_schema_path = f'{checkpoint}rawRoadsLoad_temp/schemaInfer'
cloud_storage_roads_path = f'{landing}raw_roads/'

print(cloud_storage_roads_path)
print(cloud_schema_path)

# COMMAND ----------

from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

road_schema = StructType([
        StructField('Road_ID', IntegerType()),
        StructField('Road_Category_Id', IntegerType()),
        StructField('Road_Category', StringType()),
        StructField('Region_ID', IntegerType()),
        StructField('Region_Name', StringType()),
        StructField('Total_Link_Length_Km', DoubleType()),
        StructField('Total_Link_Length_Miles', DoubleType()),
        StructField('All_Motor_Vehicles', DoubleType())
    ])

streamingDFx = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "csv") \
    .option('cloudFiles.schemaLocation', f'{checkpoint}/rawTrafficLoad/schemaInfer') \
    .option('header', 'true') \
    .schema(road_schema) \
    .load(cloud_storage_roads_path) \
    .withColumn("Extract_Time", current_timestamp())

# COMMAND ----------

display(streamingDFx)

# COMMAND ----------



# COMMAND ----------

from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType

# Replace <cloud_storage_path> with the path to your CSV files in cloud storage
cloud_schema_path = f'{checkpoint}rawRoadsLoad_temp/schemaInfer'
cloud_storage_road_path = f'{landing}/raw_roads/'
checkpointLocation = f'{checkpoint}rawRoadsLoad_temp/checkpoint'

road_schema = StructType([
        StructField('Road_ID', IntegerType()),
        StructField('Road_Category_Id', IntegerType()),
        StructField('Road_Category', StringType()),
        StructField('Region_ID', IntegerType()),
        StructField('Region_Name', StringType()),
        StructField('Total_Link_Length_Km', DoubleType()),
        StructField('Total_Link_Length_Miles', DoubleType()),
        StructField('All_Motor_Vehicles', DoubleType())
    ])

streamingDF2 = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "csv") \
    .option('cloudFiles.schemaLocation', cloud_schema_path) \
    .option('header', 'true') \
    .schema(road_schema) \
    .load(cloud_storage_road_path) \
    .withColumn("Extract_Time", current_timestamp())

# Start writing the streaming data to a Delta table
query = streamingDF2.writeStream \
    .format("delta") \
    .option("checkpointLocation", checkpointLocation) \
    .outputMode("append") \
    .toTable("db_demo_catalog.default.temp_raw_roads")

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType
from pyspark.sql.functions import current_timestamp

# Provided variables
cloud_storage_road_path = "abfss://db-demo@databricksdl101.dfs.core.windows.net/landing/raw_roads/"
cloud_schema_path = "abfss://db-demo@databricksdl101.dfs.core.windows.net/checkpoint/rawRoadsLoad_temp/schemaInfer"
checkpointLocation = "abfss://db-demo@databricksdl101.dfs.core.windows.net/checkpoint/"
road_schema = StructType([
    StructField('Road_ID', IntegerType()),
    StructField('Road_Category_Id', IntegerType()),
    StructField('Road_Category', StringType()),
    StructField('Region_ID', IntegerType()),
    StructField('Region_Name', StringType()),
    StructField('Total_Link_Length_Km', DoubleType()),
    StructField('Total_Link_Length_Miles', DoubleType()),
    StructField('All_Motor_Vehicles', DoubleType())
])
target_table = "db_demo_catalog.default.temp_raw_roads"

# Initialize Spark Session
spark = SparkSession.builder.appName("Stream Roads Data").getOrCreate()

# Reading the stream
roadStreamDF = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "csv") \
    .option("header", "true") \
    .option("cloudFiles.schemaLocation", cloud_schema_path) \
    .schema(road_schema) \
    .load(cloud_storage_road_path) \
    .withColumn("extraction_time", current_timestamp())

# Writing the stream
roadStreamDF.writeStream \
    .format("delta") \
    .option("checkpointLocation", checkpointLocation) \
    .toTable(target_table)


# COMMAND ----------

# MAGIC %md
# MAGIC ## Count
# MAGIC ## - 76
# MAGIC ## - 228
# MAGIC ## - 304
# MAGIC ## - 0

# COMMAND ----------

spark.sql("SELECT COUNT(*) FROM db_demo_catalog.default.temp_raw_roads").collect()[0][0]

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE db_demo_catalog.default.temp_raw_roads
