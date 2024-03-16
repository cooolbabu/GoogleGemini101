# Databricks notebook source

# MAGIC %md
# MAGIC # Summary
# MAGIC The code creates a schema for the orders_bronze table using StructType and StructField, and then creates a DataFrame using createDataFrame with an empty RDD.

# COMMAND ----------

# MAGIC %md
# MAGIC # Code (use Databricks workspace formatter to format the code)

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, ArrayType, TimestampType

orders_bronze_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("order_timestamp", LongType(), True),
    StructField("customer_id", StringType(), True),
    StructField("quantity", LongType(), True),
    StructField("total", IntegerType(), True),
    StructField("books", ArrayType(StructType([
        StructField("book_id", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("subtotal", LongType(), True)
    ])), True),
    StructField("_rescued_data", StringType(), True),
    StructField("file_name", StringType(), True),
    StructField("processed_timestamp", TimestampType(), True)
])

orders_bronze_df = spark.createDataFrame([], schema=orders_bronze_schema) U+0004

# COMMAND ----------

# MAGIC %md
# MAGIC # Explanation
# MAGIC 1. Import the necessary data types from pyspark.sql.types.
2. Define the schema using StructType and StructField, specifying the field names, data types, and nullability.
3. The 'books' field is an array of structs, so we use ArrayType and nest another StructType inside it.
4. Create an empty DataFrame using createDataFrame with an empty RDD and the defined schema.

This code sets up the schema for the orders_bronze table and creates an empty DataFrame with that schema. You can then use this DataFrame to read data from a source or perform further operations.

# COMMAND ----------

# MAGIC %md
# MAGIC # GenAI Instructions
# MAGIC * ## AI Role
# MAGIC You are  Azure Databricks data engineer.
    You will be given tasks and asked to write pyspark code.
    You will use best practices for writing code.
    Your response will be in JSON format with keys "summary", "code", "explanation".
    Do not include introductory line the response.
    Ensure that your response has no special characters.

# COMMAND ----------
# MAGIC %md
# MAGIC * ## Instructions (Try edit mode for visualizing table structure)
# MAGIC I will give you schema for a table. Your task is to provide pyspark code to create the table.
  orders_bronze table schema
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
