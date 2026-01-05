from flask import Flask, render_template, request, flash
from resources.app_operations import AddExpense, CreateUser, GetExpenses,DeleteExpense, LoginUser,DashboardSummary

from flask import render_template, request, redirect, session
import pandas as pd
from common.config import get_connection
import os
from resources.app_operations import ensure_tables_exist




app = Flask(__name__)
app.secret_key = "expense_tracker_secret"  

#=============================================================================================================
#                            Tables creation in Database 
#=============================================================================================================


#  ---------------------- Create Required tables -----------------------------------------------------
@app.before_first_request
def init_db():
    ensure_tables_exist()

#=============================================================================================================
#                             Expense Tracker App
#=============================================================================================================


# -------------------------- App home ----------------------------------------
@app.route("/ExpenseTracker/Home")
def home():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    user = session["user"]
    conn = get_connection("EXPT")

    query = """
        SELECT category, SUM(amount) AS total
        FROM expense_logs
        WHERE user_name = %s
        GROUP BY category
    """
    df = pd.read_sql(query, conn, params=[user])

    if df.empty:
        categories = []
        totals = []
        grand_total = 0
    else:
        categories = df["category"].tolist()
        totals = df["total"].astype(float).tolist()
        grand_total = float(df["total"].sum())

    return render_template(
        "home.html",
        username=user,
        categories=categories,
        totals=totals,
        grand_total=grand_total
    )

# ------------------------------ App login route -------------------------------------------
@app.route("/ExpenseTracker/Login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    conn = get_connection("EXPT")
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, user_password
        FROM et_users
        WHERE user_name = %s
    """, (username,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return render_template("login.html", error="User not found")

    user_id, db_pass = row
    if db_pass != password:
        return render_template("login.html", error="Invalid password")

    # 🔹 Store both id + name in session
    session["user_id"] = user_id
    session["user"] = username

    return redirect("/ExpenseTracker/Home")



# -------------------- New user creation route ---------------------------------------
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



# ---------------------------- Expense Adding ----------------------------------
@app.route("/ExpenseTracker/AddExpense", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("add_expense.html")
    
    data = {
        "USER_NAME":session["user"],
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



# ------------------------ Retriving Expenses --------------------------------
@app.route("/ExpenseTracker/GetExpenses", methods=["GET", "POST"])
def get_expenses():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("get_expenses.html")       

    data = {
        "USER_NAME":session["user"],
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

    return render_template(
        "get_expenses.html",
        expenses=res["data"]
    )


# ------------------------------- Deleting Expenses ---------------------------------
@app.route("/ExpenseTracker/DeleteOldExpenses", methods=["GET", "POST"])
def delete_expenses():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    if request.method == "GET":
        return render_template("delete_expenses.html")

    delete_type = request.form["delete_type"]

    params = {"DELETE_TYPE": delete_type}

    if delete_type == "before_date":
        params["BEFORE_DATE"] = request.form.get("before_date")

    elif delete_type == "date_range":
        params["FROM_DATE"] = request.form.get("from_date")
        params["TO_DATE"] = request.form.get("to_date")

    elif delete_type == "specific_entry":
        params["ENTRY_VALUE"] = request.form.get("entry_value")

    data = {
        "USER_NAME": session["user"],
        "PASSWORD": request.form["password"],
        "PARAMS": params
    }

    res, status = DeleteExpense(data)

    if status != 200:
        flash(res.get("error"), "error")
    else:
        flash(res.get("message"), "success")

    return render_template("delete_expenses.html")


#---------------------------------- USER PROFILE ----------------------------------------------
@app.route("/ExpenseTracker/Profile")
def profile():
    if "user_id" not in session:
        return redirect("/ExpenseTracker/Login")

    conn = get_connection("EXPT")
    cur = conn.cursor()
    cur.execute("""
        SELECT user_name, created_at
        FROM et_users
        WHERE user_id = %s
    """, (session["user_id"],))
    user = cur.fetchone()
    cur.close()

    return render_template(
        "profile.html",
        username=user[0],
        created_at=user[1]
    )

# --- SHOW PROFILE DATA (optional fetch if needed)
@app.route("/ExpenseTracker/ProfileData")
def profile_data():
    if "user_id" not in session:
        return redirect("/ExpenseTracker/Login")
    return {"user_id": session["user_id"], "username": session["user"]}


# --- EDIT PROFILE NAME ---
@app.route("/ExpenseTracker/EditProfile", methods=["POST"])
def edit_profile():
    if "user_id" not in session":
        return redirect("/ExpenseTracker/Login")

    new_name = request.form["new_name"]

    conn = get_connection("EXPT")
    cur = conn.cursor()
    cur.execute(
        "UPDATE et_users SET user_name=%s WHERE user_id=%s RETURNING user_name",
        (new_name, session["user_id"])
    )
    conn.commit()
    session["user"] = new_name
    cur.close()
    flash("Profile updated", "success")
    return redirect("/ExpenseTracker/Home")


# --- CHANGE PASSWORD ---
@app.route("/ExpenseTracker/ChangePassword", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/ExpenseTracker/Login")

    old_pass = request.form["old_pass"]
    new_pass = request.form["new_pass"]

    conn = get_connection("EXPT")
    cur = conn.cursor()

    cur.execute("SELECT user_password FROM et_users WHERE user_id=%s",
                (session["user_id"],))
    db_pass = cur.fetchone()[0]

    if old_pass != db_pass:
        flash("Old password incorrect", "error")
        return redirect("/ExpenseTracker/Home")

    cur.execute("UPDATE et_users SET user_password=%s WHERE user_id=%s",
                (new_pass, session["user_id"]))
    conn.commit()
    cur.close()

    flash("Password updated", "success")
    return redirect("/ExpenseTracker/Home")




# ---------------------- Logout -> Login page ---------------------------------------------
@app.route("/ExpenseTracker/logout")
def logout_page():
    if "user" not in session:
        return redirect("/ExpenseTracker/Login")

    return render_template("logout_confirm.html",
                           username=session["user"])


@app.route("/ExpenseTracker/confirm_logout", methods=["POST"])
def confirm_logout():
    session.clear()
    return redirect("/ExpenseTracker/Login")




# ==================================================================================
#                            ADMIN 
#===================================================================================

# ------------------------------ Admin app login ----------------------------------------
@app.route("/ExpenseTracker/Admin/Login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    username = request.form["username"]
    password = request.form["password"]

    conn = get_connection("EXPT")
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM et_admins
        WHERE admin_username=%s AND admin_password=%s
    """, (username, password))

    if not cur.fetchone():
        return render_template(
            "admin_login.html",
            error="Invalid admin credentials"
        )

    session["admin"] = username
    return redirect("/ExpenseTracker/Admin/Dashboard")

# ---------------------------- Admin app dashboard / home ---------------------------------------------
@app.route("/ExpenseTracker/Admin/Dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/ExpenseTracker/Admin/Login")

    conn = get_connection("EXPT")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM et_users")
    total_users = cur.fetchone()[0]

    cur.execute("""
        SELECT user_id, user_name, created_at
        FROM et_users
        ORDER BY created_at DESC
    """)
    users = [
        {"id": r[0], "name": r[1], "created": r[2]}
        for r in cur.fetchall()
    ]

    cur.execute("SELECT COUNT(*) FROM et_admins")
    total_admins = cur.fetchone()[0]

    cur.execute("""
        SELECT admin_id, admin_username, created_at
        FROM et_admins
        ORDER BY created_at DESC
    """)
    admins = [
        {"id": r[0], "username": r[1], "created": r[2]}
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_admins=total_admins,
        users=users,
        admins=admins
    )

# --------------------------------------- New Admin creation ---------------------------------------------
@app.route("/ExpenseTracker/Admin/Create", methods=["GET", "POST"])
def admin_create():
    if "admin" not in session:
        return redirect("/ExpenseTracker/Admin/Login")

    if request.method == "GET":
        return render_template("admin_create.html")

    username = request.form["username"].strip()
    password = request.form["password"].strip()

    conn = get_connection("EXPT")
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO et_admins (admin_username, admin_password)
            VALUES (%s, %s)
        """, (username, password))

        conn.commit()
        message = "Admin created successfully"

    except Exception as e:
        conn.rollback()
        message = "Admin already exists"

    finally:
        cur.close()
        conn.close()

    return render_template(
        "admin_create.html",
        message=message
    )

# ------------------------------ Deleting Existing user ----------------------------------------------------
@app.route("/ExpenseTracker/Admin/DeleteUser", methods=["GET", "POST"])
def admin_delete_user():
    if "admin" not in session:
        return redirect("/ExpenseTracker/Admin/Login")

    if request.method == "GET":
        return render_template("admin_user_delete.html")

    user_id = request.form["user_id"].strip()

    conn = get_connection("EXPT")
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM et_users WHERE user_id = %s",
            (user_id,)
        )

        if cur.rowcount == 0:
            message = "User not found"
        else:
            conn.commit()
            message = "User deleted successfully"

    except Exception as e:
        conn.rollback()
        message = "Error deleting user"

    finally:
        cur.close()
        conn.close()

    return render_template(
        "admin_user_delete.html",
        message=message
    )


# ------------------------------- Deleting Exisiting Admin -----------------------------------------------------
@app.route("/ExpenseTracker/Admin/DeleteAdmin", methods=["GET", "POST"])
def admin_delete_admin():
    if "admin" not in session:
        return redirect("/ExpenseTracker/Admin/Login")

    if request.method == "GET":
        return render_template("admin_delete_admin.html")

    admin_id = request.form["admin_id"].strip()

    conn = get_connection("EXPT")
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM et_admins WHERE admin_id = %s",
            (admin_id,)
        )

        if cur.rowcount == 0:
            message = "Admin not found"
        else:
            conn.commit()
            message = "Admin deleted successfully"

    except Exception:
        conn.rollback()
        message = "Error deleting admin"

    finally:
        cur.close()
        conn.close()

    return render_template(
        "admin_delete_admin.html",
        message=message
    )

# --------------------------------- Admin app logout -> user app login ----------------------------------------------------------
@app.route("/ExpenseTracker/Admin/Logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/ExpenseTracker/Login")


#====================================================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9877))
    app.run(host="0.0.0.0", port=port)

#======================================================================================================