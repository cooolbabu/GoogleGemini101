# Databricks notebook source

# MAGIC %md
# MAGIC # Summary
# MAGIC Created Orders table containing order_id, customer_id, books, total_quantity

# COMMAND ----------

# MAGIC %md
# MAGIC # Code (use Databricks workspace formatter to format the code)

# COMMAND ----------

CREATE TABLE Orders (order_id INT, customer_id INT, books STRING, total_quantity INT) U+0004

# COMMAND ----------

# MAGIC %md
# MAGIC # Explanation
# MAGIC The code creates a table named Orders with columns order_id, customer_id, books, and total_quantity. The order_id and customer_id are defined as integers, books as a string, and total_quantity as an integer.

# COMMAND ----------

# MAGIC %md
# MAGIC # GenAI Instructions
# MAGIC * ## AI Role
# MAGIC You are  Azure Databricks data engineer.
    - You will be given tasks and asked to write pyspark code.
    - You will use best practices for writing code.
    - Your response will be in JSON format with keys "summary", "code", "explanation".

# COMMAND ----------
# MAGIC %md
# MAGIC * ## Instructions (Try edit mode for visualizing table structure)
# MAGIC Create a Orders table containing order_id, customer_id, books, total_quantity
