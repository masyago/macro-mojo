from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

# Get directory of current file. The directory is used to construct paths
# for schema and data as they are located in the same directory as current file
script_dir = os.path.dirname(__file__)

# Construct absolute paths for schema and data files
schema_path = os.path.join(script_dir, "schema.sql")
data_path = os.path.join(script_dir, "data.sql")

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")


print(DATABASE_URL)
