# Databricks notebook source

# MAGIC %md
# MAGIC # Summary
# MAGIC The code creates a Spark session and defines the schema for the orders_bronze table using StructType and StructField. It then creates the orders_bronze table using the defined schema.

# COMMAND ----------

# MAGIC %md
# MAGIC # Code (use Databricks workspace formatter to format the code)

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, ArrayType, TimestampType

spark = SparkSession.builder \
    .appName("CreateOrdersBronzeTable_2023-06-09_15:30") \
    .getOrCreate()

orders_bronze_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("order_timestamp", LongType(), True),
    StructField("customer_id", StringType(), True),
    StructField("quantity", LongType(), True),
    StructField("total", IntegerType(), True),
    StructField("books", ArrayType(
        StructType([
            StructField("book_id", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("subtotal", LongType(), True)
        ])
    ), True),
    StructField("_rescued_data", StringType(), True),
    StructField("file_name", StringType(), True),
    StructField("processed_timestamp", TimestampType(), True)
])

orders_bronze = spark.createDataFrame([], schema=orders_bronze_schema)

# COMMAND ----------

# MAGIC %md
# MAGIC # Explanation
# MAGIC 1. The code starts by importing the necessary classes from PySpark: SparkSession for creating the Spark session, and StructType, StructField, StringType, LongType, IntegerType, ArrayType, and TimestampType for defining the schema.

2. It creates a Spark session using SparkSession.builder with the application name "CreateOrdersBronzeTable_2023-06-09_15:30".

3. The schema for the orders_bronze table is defined using StructType and StructField. Each field in the schema is specified with its name, data type, and nullable property.

4. The "books" field is defined as an ArrayType containing a StructType, which represents the nested structure of book details (book_id, quantity, subtotal).

5. Finally, the orders_bronze table is created using spark.createDataFrame() with an empty DataFrame and the defined schema.

This code sets up the necessary Spark session and creates the orders_bronze table with the provided schema, ready for further data processing and analysis.

# COMMAND ----------

# MAGIC %md
# MAGIC # GenAI Instructions
# MAGIC * ## AI Role
# MAGIC You are  Azure Databricks data engineer.
    You will be given tasks and asked to write spark code.
    You will use best practices for writing code.
    All the code will run within a sparksession. Added date and time to session name
    Your response will be in JSON format with keys "summary", "code", "explanation".
    Do not include introductory line the response.
    Ensure that your response has no special characters.

# COMMAND ----------
# MAGIC %md
# MAGIC * ## Instructions (Try edit mode for visualizing table structure)
# MAGIC I will give you schema for a table. You are tasked with creating a spark session and neccessary code to create the table called orders_bronze
  The schema is as follows
  root
  |-- order_id: string (nullable = true)
  |-- order_timestamp: long (nullable = true)
  |-- customer_id: string (nullable = true)
  |-- quantity: long (nullable = true)
  |-- total: integer (nullable = true)
  |-- books: array (nullable = true)
  |    |-- element: struct (containsNull = true)
  |    |    |-- book_id: string (nullable = true)
  |    |    |-- quantity: integer (nullable = true)
  |    |    |-- subtotal: long (nullable = true)
  |-- _rescued_data: string (nullable = true)
  |-- file_name: string (nullable = true)
  |-- processed_timestamp: timestamp (nullable = true)
