from flask import Flask, render_template, request, flash
from resources.app_operations import AddExpense, CreateUser, GetExpenses,DeleteOldExpenses, LoginUser
from flask import render_template, request, redirect, session
import pandas as pd
from common.config import get_connection
import os
from resources.app_operations import ensure_tables_exist

ensure_tables_exist()


app = Flask(__name__)
app.secret_key = "expense_tracker_secret"  


@app.route("/ExpenseTracker/Login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = {
        "USER_NAME": request.form["username"],
        "PASSWORD": request.form["password"]
    }

    res, status = LoginUser().post(data)

    if status != 200:
        return render_template("login.html", error=res.get("error"))

    session["user"] = data["USER_NAME"]
    return redirect("/ExpenseTracker/AddExpense")

# ---------------- CREATE USER ----------------
@app.route("/ExpenseTracker/Createuser", methods=["GET", "POST"])
def create_user():
    
    if request.method == "GET":
        return render_template("create_user.html")

    data = {
        "USER_NAME": request.form["username"],
        "PASSWORD": request.form["password"]
    }

    res, status = CreateUser().post(data)

    if status != 201:
        flash(res.get("error"), "error")
    else:
        flash(res.get("message"), "success")

    return render_template("create_user.html")



# ---------------- ADD EXPENSE ----------------
@app.route("/ExpenseTracker/AddExpense", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("add_expense.html")

    data = {
        "USER_NAME": request.form["username"],
        "PASSWORD": request.form["password"],
        "PARAMS": {
            "CATEGORY": request.form["category"],
            "DESCRIPTION": request.form["description"],
            "AMOUNT": request.form["amount"]
        }
    }

    res, status = AddExpense().post(data)

    if status != 200:
        flash(res.get("error") or res.get("message"), "error")
    else:
        flash(res.get("message"), "success")

    return render_template("add_expense.html")



# ---------------- GET EXPENSES ----------------
@app.route("/ExpenseTracker/GetExpenses", methods=["GET", "POST"])
def get_expenses():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("get_expenses.html")

    data = {
        "USER_NAME": request.form["username"],
        "PASSWORD": request.form["password"],
        "PARAMS": {
            "FROM_DATE": request.form["from_date"],
            "TO_DATE": request.form["to_date"]
        }
    }

    res, status = GetExpenses().post(data)

    if status != 200:
        flash(res.get("error"), "error")
        return render_template("get_expenses.html")

    # PASS DATAFRAME DATA TO TEMPLATE
    return render_template(
        "get_expenses.html",
        expenses=res["data"]
    )



@app.route("/ExpenseTracker/DeleteOldExpenses", methods=["GET", "POST"])
def delete_expenses():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("delete_expenses.html")

    data = {
        "USER_NAME": request.form["username"],
        "PASSWORD": request.form["password"],
        "PARAMS": {
            "BEFORE_DATE": request.form["before_date"]
        }
    }

    res, status = DeleteOldExpenses().post(data)

    if status != 200:
        flash(res.get("error"), "error")
    else:
        flash(res.get("message"), "success")

    return render_template("delete_expenses.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/ExpenseTracker/Login")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9877))
    app.run(host="0.0.0.0", port=port)