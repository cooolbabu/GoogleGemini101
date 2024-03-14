# Databricks notebook source
# MAGIC %md
# MAGIC ## Objective
# MAGIC ### - Check Bookstore data
# MAGIC ### - Create Tables in Bronze layer
# MAGIC ### - Write code to Clean up

# COMMAND ----------

# DBTITLE 1,Setup External locations
bookstore_data_location = spark.sql("describe external location `bookstoredemodata`").select("url").collect()[0][0]
orders_streaming = f"{bookstore_data_location}orders-streaming/"
orders_streaming_json = f"{bookstore_data_location}orders-json-streaming/"
customers_json = f"{bookstore_data_location}customers-json/"
books_json = f"{bookstore_data_location}books-streaming/"


print(f"Displaying External locations for Book Store demo: ")
print(f" orders_streaming: {orders_streaming}\n orders_json: {orders_streaming_json}\n customers_json: {customers_json}\n")

# COMMAND ----------


# Read Parquet files into a DataFrame
orders_streaming_json_df = spark.read.format("json").load(orders_streaming_json)
orders_streaming_df = spark.read.format("parquet").load(orders_streaming)

# Read JSON files into a DataFrame
json_df = spark.read.format("json").option("inferSchema", "true").load(customers_json)

# Read CSV files


# COMMAND ----------

display(orders_streaming_df.limit(100))

# COMMAND ----------

orders_streaming_df.show()

# COMMAND ----------

display(json_df)

# COMMAND ----------

json_df.show()

# COMMAND ----------

books_json_df = spark.read.format("json").option("inferSchema", "true").load(books_json)
books_json_df.show()

# COMMAND ----------

books_csv = f"{bookstore_data_location}books-csv/"
books_csv_df = spark.read.format("csv").option("inferSchema", "true").option("header", "true").option("delimiter", ";").load(books_csv)
books_csv_df.show()
