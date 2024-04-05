# Databricks notebook source
# MAGIC %md
# MAGIC # Summary
# MAGIC Medallion architecture implementation in Azure Databricks using PySpark
# COMMAND ----------
# MAGIC %md
# MAGIC ##Part 1: Ingesting Data into Orders_Bronze Table
# COMMAND ----------
# MAGIC %md
# MAGIC ## Explanation
This code initializes a Spark session and sets up the AutoLoader to ingest data from the specified input folder. The data is read in parquet format, and schema evolution is enabled to handle any changes in the incoming data schema. The file_name and processed_timestamp columns are appended to the DataFrame. The data is then written to the orders_bronze table in append mode, with a checkpoint location specified for fault tolerance. The trigger option 'availableNow' is used to process the available files immediately.
# COMMAND ----------
from pyspark.sql.functions import input_file_name, current_timestamp
from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName('MedallionArchitecture').getOrCreate()

# Define variables
checkpoint_location_bronze = 'dbfs:/mnt/bookstore/checkpoints/orders_bronze'
input_folder_location = 'dbfs:/mnt/bookstore/orders-raw'
target_table_bronze = 'orders_bronze'

# Ingest data using AutoLoader
bronze_df = (spark.readStream.format('cloudFiles')
    .option('cloudFiles.format', 'parquet')
    .option('cloudFiles.schemaLocation', checkpoint_location_bronze)
    .option('cloudFiles.schemaEvolutionMode', 'addNewColumns')
    .load(input_folder_location)
    .withColumn('file_name', input_file_name())
    .withColumn('processed_timestamp', current_timestamp())
)

# Write stream to target table
(bronze_df.writeStream.format('delta')
    .outputMode('append')
    .option('checkpointLocation', checkpoint_location_bronze)
    .trigger(availableNow=True)
    .toTable(target_table_bronze)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ##Part 2: Writing Orders_Silver Table from Orders_Bronze and Customers
# COMMAND ----------
# MAGIC %md
# MAGIC ## Explanation
This code reads the orders_bronze table as a stream and creates a temporary view. It then loads the customers table and performs a SQL join between the orders_bronze_streaming_view and the customers table on the customer_id. The join extracts first_name and last_name from the profile JSON column. It filters out rows with a quantity of 0 or less. The resulting DataFrame is written to the orders_silver table in append mode with a checkpoint location specified. The trigger option 'availableNow' is used to process the available data immediately.
# COMMAND ----------
from pyspark.sql.functions import from_json, col

# Define variables
orders_bronze_table = 'orders_bronze'
customers_table = 'customers'
checkpoint_location_silver = 'dbfs:/mnt/bookstore/checkpoints/orders_silver'
target_table_silver = 'orders_silver'

# Read from orders_bronze table as a stream
orders_bronze_df = spark.readStream.table(orders_bronze_table)
orders_bronze_df.createOrReplaceTempView('orders_bronze_streaming_view')

# Load customers table
customers_df = spark.read.table(customers_table)

# Perform SQL join and select order details
silver_df = spark.sql("""
    SELECT ob.order_id, ob.quantity, ob.customer_id, ob.books,
           get_json_object(c.profile, '$.first_name') AS f_name,
           get_json_object(c.profile, '$.last_name') AS l_name,
           ob.order_date
    FROM orders_bronze_streaming_view ob
    JOIN customers c ON ob.customer_id = c.customer_id
    WHERE ob.quantity > 0
""")

# Write the joined data to the orders_silver table
(silver_df.writeStream.format('delta')
    .outputMode('append')
    .option('checkpointLocation', checkpoint_location_silver)
    .trigger(availableNow=True)
    .toTable(target_table_silver)
)
# COMMAND ----------
# MAGIC %md
# MAGIC ##Part 3: Populating Sales_by_Author Table from Orders_Silver
# COMMAND ----------
# MAGIC %md
# MAGIC ## Explanation
This code reads the orders_silver table as a stream and explodes the books array to flatten the book details. It then joins the resulting DataFrame with the books table to enrich the book items with the author information. The data is grouped by author, and the total sales amount and quantity are aggregated. The aggregated data is written to the sales_by_author table using writeStream in complete output mode, which is suitable for aggregations. The checkpoint location is specified for fault tolerance, and the trigger option 'availableNow' is used to process the available data immediately.
# COMMAND ----------
from pyspark.sql.functions import explode

# Define variables
orders_silver_table = 'orders_silver'
books_table = 'books'
target_table_sales_by_author = 'sales_by_author'
checkpoint_location_sales_by_author = 'dbfs:/mnt/bookstore/checkpoints/sales_by_author'

# Read from the orders_silver table as a stream
orders_silver_df = spark.readStream.table(orders_silver_table)

# Explode the books array and select necessary columns
books_df = orders_silver_df.selectExpr('explode(books) as book', '*')

# Join with books table to enrich with author
sales_df = books_df.join(spark.table(books_table), books_df.book.book_id == spark.table(books_table).book_id)

# Group by author and aggregate
sales_by_author_df = sales_df.groupBy('author')
    .agg(sum('book.subtotal').alias('Total_Sales_Amount'),
        sum('book.quantity').alias('Total_Sales_Quantity'))

# Write the aggregated data to the sales_by_author table
(sales_by_author_df.writeStream.format('delta')
    .outputMode('complete')
    .option('checkpointLocation', checkpoint_location_sales_by_author)
    .trigger(availableNow=True)
    .toTable(target_table_sales_by_author)
)

# COMMAND ----------
# MAGIC %md
# MAGIC # GenAI Instructions
# COMMAND ----------

# MAGIC %md
# MAGIC * ## System message to AI
# MAGIC   * You are  Azure Databricks data engineer.
    - You will be given tasks and asked to write pyspark code.
    - You will use best practices for writing code.
    - Your response will be in JSON format with keys summary, number_of_parts, sub_header, code, explanation.
    - JSON format must be summary, number_of_parts and parts. Parts must be an array containing code and explanation

# COMMAND ----------
# MAGIC %md
# MAGIC * ## Instructions to AI (Try edit mode for visualizing table structure)
# MAGIC   * Please build a pyspark program for Azure Databricks using Medallion framework.
- I will give you the table schema. I will provide general instructions and instructions for each step. 
- The schema for the tables is as follows

- customers table schema
root
 |-- customer_id: string (nullable = true)
 |-- email: string (nullable = true)
 |-- profile: string (nullable = true)
 |-- updated: string (nullable = true)

- books table schema
root
 |-- book_id: string (nullable = true)
 |-- title: string (nullable = true)
 |-- author: string (nullable = true)
 |-- category: string (nullable = true)
 |-- price: double (nullable = true)
 
- orders_bronze table schema
root
 |-- order_id: string (nullable = true)
 |-- order_timestamp: long (nullable = true)
 |-- customer_id: string (nullable = true)
 |-- quantity: long (nullable = true)
 |-- total: integer (nullable = true)
 |-- books: array (nullable = true)
 |--|-- element: struct (containsNull = true)
 |--|--|--- book_id: string (nullable = true)
 |--|--|--- quantity: integer (nullable = true)
 |--|--|--- subtotal: long (nullable = true)
 |-- _rescued_data: string (nullable = true)
 |-- file_name: string (nullable = true)
 |-- processed_timestamp: timestamp (nullable = true)
 

- orders_silver schema
root
 |-- order_id: string (nullable = true)
 |-- quantity: long (nullable = true)
 |-- customer_id: string (nullable = true)
 |-- books: array (nullable = true)
 |-- |-- element: struct (containsNull = true)
 |--|--|--- book_id: string (nullable = true)
 |--|--|--- quantity: integer (nullable = true)
 |--|--|--- subtotal: long (nullable = true)
 |-- f_name: string (nullable = true)
 |-- l_name: string (nullable = true)
 |-- order_date: string (nullable = true)
 

- sales_by_author schema
root
 |-- author: string (nullable = true)
 |-- Total_Sales_Amount: long (nullable = true)
 |-- Total_Sales_Quantity: long (nullable = true)

General Instructions:

1 - Use variables following programming best practices
2 - Root directory for the checkpoint folder is dbfs:/mnt/bookstore/checkpoints/
3 - Root directory for the schemas folder is dbfs:/mnt/bookstore/schemas/
4 - Define necessary sub-folders as required. 

The instructions are given in three parts

Part 1: Ingesting Data into Orders_Bronze Table
1 - input folder location for raw data is dbfs:/mnt/bookstore/orders-raw
2 - Initialize a Spark session and use Autoloader to ingest data files. The file format is parquet.
3 - Append file_name and processed_timestamp columns using input_file_name() and current_timestamp() functions, respectively.
4 - Write the stream to target table orders_bronze table. Use Append as output mode. Specify checkpoint location.
5 - use .trigger(availableNow=True)
6 - Use toTable() function
7 - Use Autoloader schema evolution functionality
8 - Generated code for part must be placed in code value of the json object
9 - Explanation for the part must be placed in code value of the json object 


Part 2: Writing Orders_Silver Table from Orders_Bronze and Customers
1 - Table names and locations are stored in variables
1 - Read from orders_bronze table as a stream and create a temporary streaming view named orders_bronze_streaming_view.
2 - Load the customers table
3 - Perform a SQL join between orders_bronze_streaming_view and customers table on customer_id. Selecting order details. Extract first_name and last_name from profile column. Profile column is a json object.
4 - select only rows that have quantity greater than 0
5 - Write the joined data to the orders_silver table using writeStream with append mode. Specify checkpoint location.
6 - use .trigger(availableNow=True)
7 - Use toTable() function
8 - Generated code for part must be placed in code value of the json object
9 - Explanation for the part must be placed in code value of the json object 

Part 3: Populating Sales_by_Author Table from Orders_Silver
1 - Table names and locations are stored in variables
2 - Read from the orders_silver table as a stream, explode the books array to flatten the book details, and select necessary columns for processing.
3 - Assume the books table exists and contains book_id and author, perform a join to enrich book items with author.
4 - Group by author and aggregate to calculate Total_Sales_Amount and Total_Sales_Quantity.
5 - Write the aggregated data to the sales_by_author table using writeStream
6 - use .trigger(availableNow=True) 
7 - Use toTable() function
8 - Generated code for part must be placed in code value of the json object
9 - Explanation for the part must be placed in code value of the json object 
