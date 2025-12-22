from flask_restful import Resource, request
from flask import request

import pandas as pd
import numpy as np
from common.config import logger
import logging
import datetime
from datetime import datetime
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
from common.config import get_connection

#==================================================================================================
#                                   Expense Tracker App
#==================================================================================================
class LoginUser(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        if not user_name or not password:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        query = "SELECT user_password FROM et_users WHERE user_name = %s"
        df = pd.read_sql(query, conn, params=[user_name])

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != password:
            return {"error": "Invalid password"}, 401

        return {"message": "Login successful"}, 200

class DashboardSummary(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        if not user_name or not password:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        # Validate user
        query = "SELECT user_password FROM et_users WHERE user_name = %s"
        df = pd.read_sql(query, conn, params=[user_name])

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != password:
            return {"error": "Incorrect password"}, 401

        # Aggregate expenses
        agg_query = """
            SELECT category, SUM(amount) AS total
            FROM expense_logs
            WHERE user_name = %s
            GROUP BY category
        """

        df_summary = pd.read_sql(agg_query, conn, params=[user_name])

        if df_summary.empty:
            return {"categories": [], "totals": [], "grand_total": 0}, 200

        categories = df_summary["category"].tolist()
        totals = df_summary["total"].astype(float).tolist()
        grand_total = float(df_summary["total"].sum())

        return {
            "categories": categories,
            "totals": totals,
            "grand_total": grand_total
        }, 200

class AddExpense(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cursor = conn.cursor()

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        params = data.get("PARAMS", {})
        category = params.get("CATEGORY")
        description = params.get("DESCRIPTION")
        amount = params.get("AMOUNT")

        # Validate mandatory fields
        if not all([user_name, password]):
            logger.debug("USER_NAME and PASSWORD are required")
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        if not all([category, description, amount]):
            logger.debug("PARAMS must include CATEGORY, DESCRIPTION, AMOUNT")
            return {"error": "PARAMS must include CATEGORY, DESCRIPTION, AMOUNT"}, 400

        # Check user
        query = "SELECT user_id, user_name, user_password FROM et_users WHERE user_name = %s"
        df = pd.read_sql(query, conn, params=[user_name])

        if df.empty:
            logger.debug("User not found")
            return {"message": "User not found"}, 404

        row = df.iloc[0]

        if row["user_password"] != password:
            logger.debug("Password incorrect ")
            return {"message": "Incorrect password"}, 401

        user_id = int(row["user_id"])

        # Insert expense log
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_query = """
            INSERT INTO expense_logs (user_name, log_creation_date, category, description, amount)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(
            insert_query,
            (user_name, login_time, category, description, amount)
        )
        conn.commit()
        logger.debug(f"Expenses added successfully {user_name}")
        return {"message": f"Expense added for {user_name} successfully"}, 200


class CreateUser(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cursor = conn.cursor()

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        # Validate inputs
        if not user_name or not password:
            logger.debug("USER_NAME and PASSWORD are required")
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        # Check if user already exists
        check_query = "SELECT user_id FROM et_users WHERE user_name = %s"
        df = pd.read_sql(check_query, conn, params=[user_name])

        if not df.empty:
            logger.debug("User already exists")
            return {"error": "User already exists"}, 409

        # Insert new user
        insert_query = """
            INSERT INTO et_users (user_name, user_password)
            VALUES (%s, %s)
        """

        cursor.execute(insert_query, (user_name, password))
        conn.commit()
        logger.debug(f"{user_name} created successfully")
        return {"message": "User created successfully"}, 201

class GetExpenses(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cursor = conn.cursor()

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        params = data.get("PARAMS", {})
        from_date = params.get("FROM_DATE")
        to_date = params.get("TO_DATE")

        # Validate
        if not user_name or not password:
            logger.debug("USER_NAME and PASSWORD are required")
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        if not from_date or not to_date:
            logger.debug("PARAMS must include FROM_DATE and TO_DATE")
            return {
                "error": "PARAMS must include FROM_DATE and TO_DATE"
            }, 400

        # Validate user
        query = "SELECT user_id, user_password FROM et_users WHERE user_name = %s"
        df = pd.read_sql(query, conn, params=[user_name])

        if df.empty:
            logger.debug("User not found")
            return {"error": "User not found"}, 404

        row = df.iloc[0]

        if row["user_password"] != password:
            logger.debug("Incorrect password")
            return {"error": "Incorrect password"}, 401

        # Fetch expense logs in date range
        fetch_query = """
            SELECT expense_id, user_name, category, description, amount, log_creation_date
            FROM expense_logs
            WHERE user_name = %s
              AND log_creation_date::date BETWEEN %s AND %s
            ORDER BY log_creation_date DESC;
        """

        df_expenses = pd.read_sql(fetch_query, conn,
                                  params=[user_name, from_date, to_date])

        # Convert to list of dicts
        df_expenses["log_creation_date"] = df_expenses["log_creation_date"].astype(str)
        # logger.debug(result)
        # Convert dataframe to list of dicts
        result = df_expenses.to_dict(orient="records")
        return {"data": result}, 200


class DeleteOldExpenses(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cursor = conn.cursor()

        user_name = data.get("USER_NAME")
        password = data.get("PASSWORD")

        params = data.get("PARAMS", {})
        before_date = params.get("BEFORE_DATE")

        if not user_name or not password:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        if not before_date:
            return {"error": "PARAMS must include BEFORE_DATE"}, 400

        query = "SELECT user_id, user_password FROM et_users WHERE user_name = %s"
        df = pd.read_sql(query, conn, params=[user_name])

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != password:
            return {"error": "Incorrect password"}, 401

        delete_query = """
            DELETE FROM expense_logs
            WHERE user_name = %s
              AND log_creation_date::date < %s
        """

        cursor.execute(delete_query, (user_name, before_date))
        deleted_count = cursor.rowcount
        conn.commit()

        return {
            "message": f"Deleted {deleted_count} expenses before {before_date}"
        }, 200


#====================================================================================================
#                                   Tables creation in database 
#====================================================================================================
def ensure_tables_exist():
    conn = get_connection("EXPT")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS et_users (
        user_id SERIAL PRIMARY KEY,
        user_name VARCHAR(100) UNIQUE NOT NULL,
        user_password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_logs (
        expense_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        user_name VARCHAR(100),
        category VARCHAR(100),
        description TEXT,
        amount NUMERIC(10,2),
        log_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    ALTER TABLE expense_logs
    ADD COLUMN IF NOT EXISTS user_name VARCHAR(100);
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS et_admins (
    admin_id SERIAL PRIMARY KEY,
    admin_username VARCHAR(100) UNIQUE NOT NULL,
    admin_password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
                   """)
    conn.commit()
    cursor.close()
    conn.close()

