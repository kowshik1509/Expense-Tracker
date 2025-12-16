import psycopg2
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

time = datetime.now()

formatted_time = time.strftime("%y-%m-%d")
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt= '%y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f"ExpenseTracker_{formatted_time}.logs", mode='a'),  # Log to file (append mode)
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger("MyApp")

def get_connection(db_name):
        try:
            db_name = db_name.upper()
            conn = psycopg2.connect(
                user=os.getenv(f"{db_name}_DB_USER"),
                password=os.getenv(f"{db_name}_DB_PASSWORD"),
                host=os.getenv(f"{db_name}_DB_HOST"),
                port=os.getenv(f"{db_name}_DB_PORT"),
                database=os.getenv(f"{db_name}_DB_NAME")
            )
            logger.debug(f"Connected to {db_name} database.")
            return conn
        except Exception as e:
            logger.debug(f"Error while connecting to {db_name} database: {e}")
            return None