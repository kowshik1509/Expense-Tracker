📊 Expense Tracker Web Application

A full-stack Expense Tracker Web Application built using Flask, PostgreSQL, and server-rendered HTML templates.
The application allows users to securely log in, add expenses, view expenses within a date range, and delete old expense records.

This project demonstrates backend API design, database integration, HTML templating, and session-based authentication.

🚀 Features

User login with session management

Add daily expenses with category and description

View expenses within a selected date range

Delete expenses before a specific date

PostgreSQL database integration

REST-style backend operations

Reusable navigation bar across pages

Clean and responsive UI

🛠️ Tech Stack

Backend

Python

Flask

Flask-RESTful

PostgreSQL

psycopg2

pandas

Frontend

HTML5

CSS3 (embedded styling)

Jinja2 Templates

Others

python-dotenv

Logging for debugging and auditing

📂 Project Structure
Expense_Tracker/
│
├── app.py
├── requirements.txt
├── README.md
│
├── common/
│   └── config.py
│
├── resources/
│   └── app_operations.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── create_user.html
│   ├── add_expense.html
│   ├── get_expenses.html
│   └── delete_expenses.html
│
├── logs/
│   └── ExpenseTracker_YYYY-MM-DD.logs

⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone <your-repo-url>
cd Expense_Tracker

2️⃣ Create Virtual Environment (Optional but Recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

🔐 Environment Variables

Create a .env file in the project root:

EXPT_DB_HOST=localhost
EXPT_DB_NAME=Expt_db
EXPT_DB_USER=postgres
EXPT_DB_PASSWORD=your_password
EXPT_DB_PORT=5432

▶️ Run the Application
python app.py


Open your browser and visit:

http://127.0.0.1:9877/login

🔗 Application Routes
Route	Description
/login	User login page
/ExpenseTracker/Createuser	Create new user
/ExpenseTracker/AddExpense	Add expense
/ExpenseTracker/GetExpenses	View expenses
/ExpenseTracker/DeleteOldExpenses	Delete old expenses
/logout	Logout user
🧠 Design Highlights

Separation of Concerns:
Database and business logic are handled in app_operations.py, while routing and rendering are managed in app.py.

Reusable Templates:
Common UI elements (navbar, layout) are centralized in base.html.

Session-Based Authentication:
Ensures secure access to application features.