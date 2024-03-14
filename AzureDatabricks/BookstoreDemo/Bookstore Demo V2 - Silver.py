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

# MAGIC %md
# MAGIC ## Stage 2 - Order data from Bronze to Silver layer

# COMMAND ----------

# DBTITLE 1,Logging for Validation
orders_count_query = f"SELECT COUNT(*) as r_count FROM {ordersFactsTBL}"
r_count = spark.sql(orders_count_query).collect()[0]["r_count"]

print(f"Number of rows in {ordersFactsTBL} (before): {r_count}")

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

query.awaitTermination()


# COMMAND ----------

# DBTITLE 1,Logging for Validation
orders_count_query = f"SELECT COUNT(*) as r_count FROM {ordersFactsTBL}"
r_count = spark.sql(orders_count_query).collect()[0]["r_count"]

print(f"Number of rows in {ordersFactsTBL} (after): {r_count}")
