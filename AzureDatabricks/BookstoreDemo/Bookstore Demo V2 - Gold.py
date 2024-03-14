# Databricks notebook source
# MAGIC %md
# MAGIC # Intialize

# COMMAND ----------

# DBTITLE 1,Gold layer processing Metadata
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

# DBTITLE 1,Logging for validation
query = f"SELECT * FROM {sales_by_authorTBL} ORDER BY  Total_Sales_Amount DESC"
print("Sales by author(before): ")
spark.sql(query).display()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 3 - Order data from Silver to Gold layer

# COMMAND ----------

# DBTITLE 1,ChatGPT Generated code
from pyspark.sql.functions import explode, col, sum as _sum

# Read from orders_silver table as a stream
ordersSilverStream = spark.readStream.table(f"{ordersFactsTBL}")

# Explode the books array to work with each book individually
# Then, join with the books table to get the author's name for each book
# Finally, aggregate to calculate total sales amount and quantity by author
salesByAuthorDF = ordersSilverStream \
    .selectExpr("explode(books) as book", "order_id") \
    .select(
        col("book.book_id"),
        col("book.quantity"),
        col("book.subtotal"),
        col("order_id")
    ) \
    .join(spark.table(f"{booksTBL}"), "book_id") \
    .groupBy("author") \
    .agg(
        _sum("subtotal").alias("Total_Sales_Amount"),
        _sum("quantity").alias("Total_Sales_Quantity")
    )

# Write the aggregated data to sales_by_author table, triggering once available data is processed
salesByAuthorDF.writeStream \
    .outputMode("complete") \
    .option("checkpointLocation", f"{bookstore_checkpoints}/sales_by_author") \
    .trigger(availableNow=True) \
    .toTable(f"{sales_by_authorTBL}")




# COMMAND ----------

# DBTITLE 1,Logging for validation
query = f"SELECT * FROM {sales_by_authorTBL} ORDER BY  Total_Sales_Amount DESC"
print("Sales by author(after): ")
spark.sql(query).display()
