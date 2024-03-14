# Databricks notebook source
bookstore_data_location = spark.sql("describe external location `bookstoredemodata`").select("url").collect()[0][0]


checkpoints = f"{bookstore_data_location}checkpoints/"
schemas = f"{bookstore_data_location}schemas/"
landing_orders = f"{bookstore_data_location}orders-raw/"
bronze = f"{bookstore_data_location}bronze/"
silver = f"{bookstore_data_location}silver/"
gold = f"{bookstore_data_location}gold/"

print(f"Folder locations \n{checkpoints}\n{schemas}\n{landing_orders}\n{bronze}\n{silver}\n{gold}")

# COMMAND ----------


