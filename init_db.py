from common.config import get_connection, logger

conn = get_connection("EXPT")
cursor = conn.cursor()

# ⚠️ DROP tables if they exist (order matters because of FK)
cursor.execute("""
DROP TABLE IF EXISTS expense_logs CASCADE;
""")

cursor.execute("""
DROP TABLE IF EXISTS et_users CASCADE;
""")

# ✅ Recreate tables
cursor.execute("""
CREATE TABLE et_users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE NOT NULL,
    user_password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE expense_logs (
    expense_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    user_name VARCHAR(100),
    category VARCHAR(100),
    description TEXT,
    amount NUMERIC(10,2),
    log_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES et_users(user_id)
        ON DELETE CASCADE
);
""")

conn.commit()
cursor.close()
conn.close()

logger.debug("Tables dropped and recreated successfully")
