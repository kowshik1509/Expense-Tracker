import psycopg2
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

formatted_time = datetime.now().strftime("%Y-%m-%d")

log_file_path = os.path.join(
    LOG_DIR, f"ExpenseTracker_{formatted_time}.logs"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode="a"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ExpenseTracker")

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