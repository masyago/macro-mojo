from dotenv import load_dotenv
import logging
import os
import psycopg2

load_dotenv()
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# Configure logging messages. Log INFO messages and higher severity messages
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Get directory of current file. The directory is used to construct paths
# for schema and data as they are located in the same directory as current file
script_dir = os.path.dirname(__file__)

# Construct absolute paths for schema and data files
schema_path = os.path.join(script_dir, "schema.sql")
data_path = os.path.join(script_dir, "data.sql")

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to database
logger.info("Connecting to database")

connection = psycopg2.connect(DATABASE_URL)
cursor = connection.cursor()

# Execute schema file
logger.info(
    "Executing schema file %s",
    schema_path,
)
with open(schema_path, "r") as file:
    cursor.execute(file.read())

# Execute data seeding file
logger.info(
    "Executing data file %s",
    data_path,
)
with open(data_path, "r") as file:
    cursor.execute(file.read())

connection.commit()
connection.close()
logger.info("Database connection closed")
