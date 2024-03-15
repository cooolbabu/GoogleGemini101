# Databricks notebook source

# MAGIC %md
# MAGIC # Summary
# MAGIC The code creates a schema for the orders_bronze table using StructType and StructField classes from pyspark.sql.types, and then creates the table using createOrReplaceTempView method.

# COMMAND ----------

# MAGIC %md
# MAGIC # Code (use Databricks workspace formatter to format the code)

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, ArrayType, TimestampType  orders_bronze_schema = StructType([     StructField("order_id", StringType(), True),     StructField("order_timestamp", LongType(), True),     StructField("customer_id", StringType(), True),     StructField("quantity", LongType(), True),     StructField("total", IntegerType(), True),     StructField("books", ArrayType(         StructType([             StructField("book_id", StringType(), True),             StructField("quantity", IntegerType(), True),             StructField("subtotal", LongType(), True)         ])     ), True),     StructField("_rescued_data", StringType(), True),     StructField("file_name", StringType(), True),     StructField("processed_timestamp", TimestampType(), True) ])  orders_bronze_df = spark.createDataFrame([], schema=orders_bronze_schema) orders_bronze_df.createOrReplaceTempView("orders_bronze") U+0004

# COMMAND ----------

# MAGIC %md
# MAGIC # Explanation
# MAGIC The code first imports the necessary classes from pyspark.sql.types to define the schema. It then creates a StructType object called orders_bronze_schema that defines the structure of the table. Each field is defined using a StructField object, specifying the name, data type, and whether it can contain null values. The books field is an array of structs, so it is defined using ArrayType and a nested StructType. Finally, an empty DataFrame is created using the defined schema and registered as a temporary view named "orders_bronze" using the createOrReplaceTempView method. This allows the table to be queried using SQL.

# COMMAND ----------

# MAGIC %md
# MAGIC # GenAI Instructions
# MAGIC * ## AI Role
# MAGIC You are  Azure Databricks data engineer.
    - You will be given tasks and asked to write pyspark code.
    - You will use best practices for writing code.
    - Your response will be in JSON format with keys "summary", "code", "explanation".
    - Do not include introductory line the respoonse.

# COMMAND ----------
# MAGIC %md
# MAGIC * ## Instructions (Try edit mode for visualizing table structure)
# MAGIC - I will give you schema for a table. Your task is to provide pyspark code to create the table. 
  orders_bronze table schema
  - root
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
