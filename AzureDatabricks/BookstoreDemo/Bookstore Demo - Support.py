# Databricks notebook source
# MAGIC %md
# MAGIC # Cleanup

# COMMAND ----------

# Terminate all active streams
for stream in spark.streams.active:
    stream.stop()

# COMMAND ----------

# Drop all tables in bookstore_catalog
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.bronze.books")
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.bronze.books_temp")
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.bronze.customers")
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.bronze.orders")
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.silver.orders_facts")
spark.sql("DROP TABLE IF EXISTS bookstore_catalog.gold.sales_by_author")


# COMMAND ----------

spark.sql("DELETE FROM bookstore_catalog.bronze.orders")
spark.sql("DELETE FROM bookstore_catalog.silver.orders_facts")
spark.sql("DELETE FROM bookstore_catalog.gold.sales_by_author")

# COMMAND ----------

# Set the spark.databricks.delta.retentionDurationCheck.enabled configuration to false
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

# COMMAND ----------

# MAGIC %sql
# MAGIC VACUUM bookstore_catalog.bronze.orders RETAIN 0 HOURS DRY RUN

# COMMAND ----------

# MAGIC %sql
# MAGIC VACUUM bookstore_catalog.bronze.orders RETAIN 0 HOURS

# COMMAND ----------

# Review mount points. And capture bookstore mount point
bookstoreMP = '/mnt/bookstore'
bookstore_checkpoints = '/mnt/bookstore/checkpoints'
dbutils.fs.mounts()

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

dbutils.fs.rm(bookstore_landing_orders, recurse=True)
dbutils.fs.rm(bookstore_checkpoints, recurse=True)
dbutils.fs.mkdirs(bookstore_landing_orders)

# COMMAND ----------

# MAGIC %md
# MAGIC # Run

# COMMAND ----------

# MAGIC %run ./Helper_functions

# COMMAND ----------

load_new_data()

# COMMAND ----------

# MAGIC %md
# MAGIC # Validate

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT * FROM bookstore_catalog.gold.sales_by_author ORDER BY  Total_Sales_Amount DESC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT 
# MAGIC   b.author AS Author, 
# MAGIC   COALESCE(SUM(o.books[0].subtotal), 0) AS Total_Sales_Amount,
# MAGIC   COALESCE(SUM(o.books[0].quantity), 0) AS Total_Sales_Quantity
# MAGIC FROM 
# MAGIC   bookstore_catalog.silver.orders_facts o
# MAGIC LEFT JOIN 
# MAGIC   bookstore_catalog.bronze.books b ON o.books[0].book_id = b.book_id
# MAGIC GROUP BY 
# MAGIC   b.author
# MAGIC ORDER BY 
# MAGIC   Total_Sales_Amount DESC
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC # Setup Customers and Books tables

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE SCHEMA IF NOT EXISTS bookstore_catalog.gold;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE TABLE bookstore_catalog.bronze.customers AS
# MAGIC SELECT * FROM json.`/mnt/bookstore/customers-json`;

# COMMAND ----------

books_csv_path = f"{bookstoreMP}/books-csv/export_*.csv"  # Adjust based on actual path structure

books_df = spark.read.format("csv") \
    .option("header", "true") \
    .option("delimiter", ";") \
    .schema("book_id STRING, title STRING, author STRING, category STRING, price DOUBLE") \
    .load(books_csv_path)
books_df.write.saveAsTable("bookstore_catalog.bronze.books")


# COMMAND ----------

# MAGIC %md
# MAGIC # Table counts

# COMMAND ----------

customer_count_query = "SELECT COUNT(*) as customer_count FROM bookstore_catalog.bronze.customers"
books_count_query = "SELECT COUNT(*) as books_count FROM bookstore_catalog.bronze.books"

customer_count = spark.sql(customer_count_query).collect()[0]["customer_count"]
books_count = spark.sql(books_count_query).collect()[0]["books_count"]

print(f"Number of rows in bronze.customer: {customer_count}")
print(f"Number of rows in bronze.books: {books_count}")

# COMMAND ----------

spark.sql("SELECT * FROM bookstore_catalog.bronze.customers").display()

# COMMAND ----------

spark.sql("SELECT * FROM bookstore_catalog.bronze.books").display()

# COMMAND ----------

# MAGIC %sql
# MAGIC /* Show orders loaded into orders table in bronze schema */
# MAGIC SELECT "Number of orders in bronze.orders: " , count(*) FROM bookstore_catalog.bronze.orders
# MAGIC
# MAGIC /* There 1000 orders per file and 9 files total */

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(*) from bookstore_catalog.silver.orders_facts
# MAGIC
# MAGIC /* There 1000 orders per file and 9 files total */

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(*) from bookstore_catalog.gold.sales_by_author
# MAGIC
# MAGIC /* There are 12 Authors */

# COMMAND ----------

books_csv = f"{bookstoreMP}/books-csv/"
books_csv_df = spark.read.format("csv").option("inferSchema", "true").option("header", "true").option("delimiter", ";").load(books_csv)
books_csv_df.show()

# COMMAND ----------

# MAGIC %md
# MAGIC
