# Databricks notebook source
# MAGIC %md
# MAGIC # Intialize

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
# MAGIC # Go Medallion

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 1 - Load Data into Bronze table

# COMMAND ----------

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

# MAGIC %md
# MAGIC ## Stage 2 - Order data from Bronze to Silver layer

# COMMAND ----------

from pyspark.sql.functions import col, get_json_object, from_unixtime


# Read the streaming dataset from orders.orders table
ordersStream = spark.readStream.format("delta").table(f"{ordersTBL}")

# Assuming customers is a static table, read it as a DataFrame
customers = spark.table(f"{customersTBL}")

# Join the streaming DataFrame with the static DataFrame
joinedStream = ordersStream.join(customers, ordersStream.customer_id == customers.customer_id, "inner") \
    .select(
        ordersStream.order_id,
        ordersStream.quantity,
        ordersStream.customer_id,
        ordersStream.books,
        get_json_object(col("customers.profile"), "$.first_name").alias("f_name"),
        get_json_object(col("customers.profile"), "$.last_name").alias("l_name"),
        from_unixtime("orders.order_timestamp", 'yyyy-MM-dd HH:mm:ss').alias("order_date"),      
    )

# Create a temporary view with the result
#joinedStream.createOrReplaceTempView("orders_customers_view")
query = joinedStream.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", f"{bookstore_checkpoints}/checkpoints/orders_silver") \
    .trigger(availableNow=True) \
    .toTable(f"{ordersFactsTBL}")

                                                                       


# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 3 - Order data from Silver to Gold layer

# COMMAND ----------

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

