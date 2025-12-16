from common.config import get_connection, logger

conn = get_connection("EXPT")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS et_users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE NOT NULL,
    user_password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS expense_logs (
    expense_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES et_users(user_id) ON DELETE CASCADE,
    user_name varchar(100),
    category VARCHAR(100),
    description TEXT,
    amount NUMERIC(10,2),
    log_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")


conn.commit()
cursor.close()
conn.close()

logger.debug("Tables created and default user added")
