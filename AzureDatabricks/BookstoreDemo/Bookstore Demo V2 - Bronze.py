# Databricks notebook source
# MAGIC %md
# MAGIC ## Intialize

# COMMAND ----------

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Bookstore Data Ingestion").getOrCreate()
# Set Spark configuration for Bookstore demo data
bookstore_data_location = spark.sql("describe external location `bookstoredemodata`").select("url").collect()[0][0]
spark.conf.set(f"dataset.bookstore", bookstore_data_location)
spark.conf.set(f"bookstoreDB", "bookstore_catalog")
bookstoreDB = "bookstore_catalog"


bookstore_checkpoints = f"{bookstore_data_location}checkpoints/"
bookstore_schemas = f"{bookstore_data_location}schemas/"
bookstore_landing_orders = f"{bookstore_data_location}orders-raw/"
bookstore_streaming_orders = f"{bookstore_data_location}orders-streaming/"
bookstore_bronze = f"{bookstore_data_location}bronze/"
bookstore_silver = f"{bookstore_data_location}silver/"
bookstore_gold = f"{bookstore_data_location}gold/"

# Setup mountpoints
bookstoreMP = '/mnt/bookstore'
bookstore_checkpoints = '/mnt/bookstore/checkpoints'

# print(f"Folder locations \n{bookstore_checkpoints}\n{bookstore_schemas}\n{bookstore_landing_orders}\n{bookstore_streaming_orders}\n{bookstore_bronze}\n{bookstore_silver}\n{bookstore_gold}")

# Tables
customersTBL = "bookstore_catalog.bronze.customers"
booksTBL = "bookstore_catalog.bronze.books"
ordersTBL= "bookstore_catalog.bronze.orders"
ordersFactsTBL = "bookstore_catalog.silver.orders_facts"
sales_by_authorTBL = "bookstore_catalog.gold.sales_by_author"


# COMMAND ----------

customer_count_query = f"SELECT COUNT(*) as customer_count FROM {customersTBL}"
books_count_query = f"SELECT COUNT(*) as books_count FROM {booksTBL}"

customer_count = spark.sql(customer_count_query).collect()[0]["customer_count"]
books_count = spark.sql(books_count_query).collect()[0]["books_count"]

print(f"Number of rows in bronze.customer: {customer_count}")
print(f"Number of rows in bronze.books: {books_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 1 - Load Data into Bronze table

# COMMAND ----------

# DBTITLE 1,Logging for validation

orders_count_query = f"SELECT COUNT(*) as r_count FROM {ordersTBL}"
r_count = spark.sql(orders_count_query).collect()[0]["r_count"]

print(f"Number of rows in {ordersTBL} (before): {r_count}")


# COMMAND ----------

# DBTITLE 1,ChatGPT Code
from pyspark.sql import SparkSession
from pyspark.sql.functions import input_file_name, current_timestamp

# Initialize Spark Session for Databricks
spark = SparkSession.builder.appName("StructuredStreamingMedallionArchitecture").getOrCreate()

# Read stream from raw data folder
ordersRawStream = (spark
                   .readStream
                   .format("cloudFiles")
                   .option("cloudFiles.format", "parquet")
                   .option("cloudFiles.schemaLocation", f"{bookstore_checkpoints}/orders_bronze_schema")
                   .load(f"{bookstore_landing_orders}"))

# Add file_name and processed_timestamp columns
ordersBronzeDF = ordersRawStream.withColumn("file_name", input_file_name())\
                                .withColumn("processed_timestamp", current_timestamp())

# Write stream to orders table
ordersBronzeDF.writeStream\
              .format("delta")\
              .option("checkpointLocation", f"{bookstore_checkpoints}/orders_bronze")\
              .outputMode("append")\
              .trigger(availableNow=True) \
              .toTable(f"{ordersTBL}")



# COMMAND ----------

# DBTITLE 1,Logging for validation
orders_count_query = f"SELECT COUNT(*) as r_count FROM {ordersTBL}"
r_count = spark.sql(orders_count_query).collect()[0]["r_count"]

print(f"Number of rows in {ordersTBL} (after): {r_count}")
