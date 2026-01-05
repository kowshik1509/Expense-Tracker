from flask_restful import Resource
from flask import request
import pandas as pd
from common.config import get_connection, logger
from datetime import datetime


class LoginUser(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        user = data.get("USER_NAME")
        pwd = data.get("PASSWORD")

        if not user or not pwd:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        df = pd.read_sql(
            "SELECT user_password FROM et_users WHERE user_name=%s",
            conn, params=[user]
        )

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != pwd:
            return {"error": "Invalid password"}, 401

        return {"message": "Login successful"}, 200


class DashboardSummary(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        user = data.get("USER_NAME")
        pwd = data.get("PASSWORD")

        if not user or not pwd:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        df = pd.read_sql(
            "SELECT user_password FROM et_users WHERE user_name=%s",
            conn, params=[user]
        )

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != pwd:
            return {"error": "Incorrect password"}, 401

        df = pd.read_sql("""
            SELECT category, SUM(amount) total
            FROM expense_logs
            WHERE user_name=%s
            GROUP BY category
        """, conn, params=[user])

        if df.empty:
            return {"categories": [], "totals": [], "grand_total": 0}, 200

        return {
            "categories": df["category"].tolist(),
            "totals": df["total"].astype(float).tolist(),
            "grand_total": float(df["total"].sum())
        }, 200


class AddExpense(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cur = conn.cursor()

        user = data.get("USER_NAME")
        pwd = data.get("PASSWORD")
        p = data.get("PARAMS", {})

        if not user or not pwd:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        if not all([p.get("CATEGORY"), p.get("DESCRIPTION"), p.get("AMOUNT")]):
            return {"error": "Missing CATEGORY / DESCRIPTION / AMOUNT"}, 400

        df = pd.read_sql(
            "SELECT user_password FROM et_users WHERE user_name=%s",
            conn, params=[user]
        )

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != pwd:
            return {"error": "Incorrect password"}, 401

        cur.execute("""
            INSERT INTO expense_logs (user_name, log_creation_date, category, description, amount)
            VALUES (%s,%s,%s,%s,%s)
        """, (user, datetime.now(), p["CATEGORY"], p["DESCRIPTION"], p["AMOUNT"]))

        conn.commit()
        return {"message": "Expense added successfully"}, 200


class CreateUser(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")
        cur = conn.cursor()

        user = data.get("USER_NAME")
        pwd = data.get("PASSWORD")

        if not user or not pwd:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        df = pd.read_sql(
            "SELECT user_id FROM et_users WHERE user_name=%s",
            conn, params=[user]
        )

        if not df.empty:
            return {"error": "User already exists"}, 409

        cur.execute("""
            INSERT INTO et_users (user_name, user_password)
            VALUES (%s,%s)
        """, (user, pwd))

        conn.commit()
        return {"message": "User created successfully"}, 201


class GetExpenses(Resource):
    def post(self, data=None):
        if data is None:
            data = request.get_json()

        conn = get_connection("EXPT")

        user = data.get("USER_NAME")
        pwd = data.get("PASSWORD")
        p = data.get("PARAMS", {})

        if not user or not pwd:
            return {"error": "USER_NAME and PASSWORD are required"}, 400

        if not p.get("FROM_DATE") or not p.get("TO_DATE"):
            return {"error": "FROM_DATE and TO_DATE required"}, 400

        df = pd.read_sql(
            "SELECT user_password FROM et_users WHERE user_name=%s",
            conn, params=[user]
        )

        if df.empty:
            return {"error": "User not found"}, 404

        if df.iloc[0]["user_password"] != pwd:
            return {"error": "Incorrect password"}, 401

        df = pd.read_sql("""
            SELECT expense_id, category, description, amount, log_creation_date
            FROM expense_logs
            WHERE user_name=%s
              AND log_creation_date::date BETWEEN %s AND %s
            ORDER BY log_creation_date DESC
        """, conn, params=[user, p["FROM_DATE"], p["TO_DATE"]])

        df["log_creation_date"] = df["log_creation_date"].astype(str)

        return {"data": df.to_dict(orient="records")}, 200


def DeleteExpense(data):
    conn = get_connection("EXPT")
    cur = conn.cursor()

    user = data.get("USER_NAME")
    pwd = data.get("PASSWORD")
    p = data.get("PARAMS", {})

    if not user or not pwd:
        return {"error": "USER_NAME and PASSWORD are required"}, 400

    df = pd.read_sql(
        "SELECT user_password FROM et_users WHERE user_name=%s",
        conn, params=[user]
    )

    if df.empty:
        return {"error": "User not found"}, 404

    if df.iloc[0]["user_password"] != pwd:
        return {"error": "Incorrect password"}, 401

    sql = "DELETE FROM expense_logs WHERE user_name=%s"
    args = [user]

    mode = p.get("DELETE_TYPE")

    if mode == "before_date":
        sql += " AND log_creation_date::date < %s"
        args.append(p["BEFORE_DATE"])

    elif mode == "date_range":
        sql += " AND log_creation_date::date BETWEEN %s AND %s"
        args.extend([p["FROM_DATE"], p["TO_DATE"]])

    elif mode == "specific_entry":
        sql += " AND (expense_id=%s OR description ILIKE %s)"
        args.extend([p["ENTRY_VALUE"], f"%{p['ENTRY_VALUE']}%"])

    cur.execute(sql, tuple(args))
    count = cur.rowcount
    conn.commit()

    return {"message": f"{count} record(s) deleted"}, 200


def ensure_tables_exist():
    conn = get_connection("EXPT")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS et_users (
        user_id SERIAL PRIMARY KEY,
        user_name VARCHAR(100) UNIQUE NOT NULL,
        user_password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expense_logs (
        expense_id SERIAL PRIMARY KEY,
        user_name VARCHAR(100),
        category VARCHAR(100),
        description TEXT,
        amount NUMERIC(10,2),
        log_creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS et_admins (
        admin_id SERIAL PRIMARY KEY,
        admin_username VARCHAR(100) UNIQUE NOT NULL,
        admin_password VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
