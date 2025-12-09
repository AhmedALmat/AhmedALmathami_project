# AhmedALmathami_project

# Expense Tracker — Streamlit Application

A simple, user-friendly web application for tracking personal expenses. This project allows users to add expenses, filter and view them, manage categories, visualize spending trends, and export data — all through an intuitive Streamlit interface.

# Features Overview

Add expenses with date, amount, category, and description

Quick-entry amount buttons (+5, +10, +20)

Manage custom categories (add/delete)

Filter expenses by date, category, or keywords

View summaries (by date, month, category)

Dashboard with spending charts (Altair/Streamlit)

Edit or delete individual entries

Undo last addition

Export filtered or full dataset to CSV

Persistent data stored in data/expenses.csv

# Installation Guide

1. Requirements

Python 3.10 or above (I developed the app using Python 3.11)

Git (optional but recommended)

Verify Python version: python --version

2. Clone or Download the Project: git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO. Or download ZIP files dierctly. 

3. Install Project Dependencies

pip install -r requirements.txt 
This installs: treamlit, pandas , and Altair . 

4. Run the Application

streamlit run app.py
This will open the app automatically in your browser. 

# Project Setup Details

The first time you run the app, it will automatically create:

* data/expenses.csv

Stores all expense rows.

* data/categories.json

Stores user-defined categories.

* data/reports/

Holds exported CSV files.

No API keys or external services are required.

# How to Use the Application (Step-by-Step Guide)

1. Dashboard

Shows quick stats:
Total spending
Number of entries
Start and end dates
Recent expenses
Category breakdown (chart)
Monthly spending trend

2. Add Expense

Choose date
Enter amount
Use quick buttons (+5, +10, +20) for faster input
Select existing category or add a new one
Provide optional description

3. View & Filter

Filter expenses by:
Category
Start & end date
Keyword search

You can then view results in a table and Download filtered rows as CSV

4. Summaries

Three tabs:

• By Category: Bar chart + table

• By Date: Daily totals + line chart

• By Month: Monthly totals + line chart


5. Edit Entry

Choose an entry from a list

Modify date, amount, description, category

Save changes


6. Delete

Two features:

Delete any selected entry

Undo last added entry

7. Export Data

Download:

Filtered results

All expenses

CSV files download directly through Streamlit.


8. Categories Page

Add or delete categories stored in categories.json.


# Common Errors & How to Fix Them

1. “Amount must be a number”
Cause: You entered letters or symbols instead of a number.
Fix: Enter a valid numeric amount (e.g., 12.50).

2. “Key already exists in session_state”
Cause: Streamlit widget keys conflicted internally.
Fix: Refresh the page or restart Streamlit.

3. “No expenses yet”
Cause: Your expenses file is empty.
Fix: Add your first expense using the Add Expense page.

4. “Cannot delete entry XYZ”
Cause: You clicked “Delete” without selecting an entry.
Fix: Select a valid entry from the dropdown before deleting

# Project folder Structure 

project/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
├── data/
│   ├── expenses.csv
│   ├── categories.json
│   └── reports/
│
└── docs/
    ├── Revised_Project_Spec.pdf
    ├── Version_1_Review.pdf
    └── program spec.pdf


## Thank You for Using the Expense Tracker!

Feel free to enhance, fork, or customize the project.


