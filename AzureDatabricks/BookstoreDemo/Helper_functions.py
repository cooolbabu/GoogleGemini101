# Databricks notebook source
dbutils.widgets.text(name="debug",defaultValue="False",label='Enter the environment in lower case')
env = dbutils.widgets.get("debug")

# COMMAND ----------

# Structured Streaming
streaming_dir = f"/mnt/bookstore/orders-streaming"
raw_dir = f"/mnt/bookstore/orders-raw"

def get_index(dir):
    files = dbutils.fs.ls(dir)
    index = 0
    if files:
        file = max(files).name
        index = int(file.rsplit('.', maxsplit=1)[0])
    return index+1

def load_file(current_index):
    latest_file = f"{str(current_index).zfill(2)}.parquet"
    print(f"Loading {latest_file} file to the bookstore dataset")
    dbutils.fs.cp(f"{streaming_dir}/{latest_file}", f"{raw_dir}/{latest_file}")

    
def load_new_data(all=False):
    index = get_index(raw_dir)
    if index >= 10:
        print("No more data to load\n")

    elif all == True:
        while index <= 10:
            load_file(index)
            index += 1
    else:
        load_file(index)
        index += 1

# COMMAND ----------

tenant_id = dbutils.secrets.get(scope="databricks-kv2023-2", key="tenant-id")
subscription_id = dbutils.secrets.get(scope="databricks-kv2023-2", key="subscription-id")
application_id = dbutils.secrets.get(scope="databricks-kv2023-2", key="application-id")
secret_id = dbutils.secrets.get(scope="databricks-kv2023-2", key="db1-secret")

storage_account_name = "databricksdl101"
db0storage_connection_string = dbutils.secrets.get(scope="databricks-kv2023-2", key="databricksdl101")

dataset_bookstore = 'dbfs:/mnt/bookstore'

def mount_point_exist(mount_point, mounts):
    
    exists = any(mount.mountPoint == mount_point for mount in mounts)
    if exists:
        print(f"Mount point '{mount_point}' is configured.")
        return True
    else:
        print(f"Mount point '{mount_point}' does not exist.")
        return False

def create_mounts(mount_point, container_name):
  configs = {"fs.azure.account.auth.type": "OAuth",
            "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
            "fs.azure.account.oauth2.client.id": application_id,
            "fs.azure.account.oauth2.client.secret": secret_id,
            "fs.azure.account.oauth2.client.endpoint": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"}

  # Optionally, you can add <directory-name> to the source URI of your mount point.
  dbutils.fs.mount(
    source = f"abfss://{container_name}@databricksdl101.dfs.core.windows.net/",
    mount_point = f"/mnt/{mount_point}",
    extra_configs = configs)

