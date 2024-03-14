# Databricks notebook source
# MAGIC %md
# MAGIC ### Some code snippets that where we can use python function to do interesting stuff.
# MAGIC ### Need to check out reload functionality

# COMMAND ----------

# Define your Python code as a string
python_code = """
def greet(name):
    print("Hello,", name)

greet("Alice")
"""

# Execute the Python code stored in the string
exec(python_code)


# COMMAND ----------

code_to_execute = """
sql_statement = "ALTER TABLE bookstore_catalog.bronze.orders ADD COLUMNS (col5 STRING, col6 INT);"

# Execute the SQL statement
spark.sql(sql_statement)
"""



# COMMAND ----------

exec(code_to_execute)
