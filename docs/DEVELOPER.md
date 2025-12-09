# Developer Guide — Expense Tracker (Streamlit)

This document is for developers who need to understand, maintain, or extend the Expense Tracker application. It assumes that you have already read the main user-facing `README.md` and are able to run the app with:

```bash
streamlit run app.py

# 1. Overview

The Expense Tracker is a small personal finance application built with Python, Streamlit, and pandas. It stores expenses in a CSV file and categories in a JSON file, and provides:
- A dashboard with metrics and charts
- A form-based interface to add expenses
- Filtering and export tools
- Editing and deletion of entries
- Category management (add/delete categories)
- Optional monthly budget warnings per category

The main goals are:
- Keep the code understandable for beginners
- Use simple, file-based persistence (no database)
- Provide a clean structure that can be extended later

# 2. Implemented Spec (Condensed)

From the original project specification and revisions, the following features are implemented:
- CLI prototype evolved into a Streamlit app (app.py)
- Persistent storage in data/expenses.csv
- Category storage in data/categories.json with UI to add/delete categories

Pages:

    - Dashboard (metrics, category chart, monthly trend)
    - Add Expense (with quick-entry amount buttons)
    - View & Filter (category, date range, keyword)
    - Summaries (by category, date, month)
    - Edit Entry (with filters and dropdown selection)
    - Delete (by entry + undo last addition)
    - Export (filtered view / all data)
    - Categories (manage category list)
- Basic error handling and input validation
- Simple monthly budget warnings per category

Planned but not fully implemented features (or partially implemented):

- Advanced chart formatting and theming
- More robust large-data performance strategies
- More flexible budget logic and multiple profiles

# 3. Install / Deployment / Admin Notes

- Most deployment details are already in the main README.md. This section adds extra developer-relevant information.
- Python version: Project developed with Python 3.11 (3.10+ recommended).
- Dependencies:
  - streamlit
  - pandas
  - altair
- All dependencies are listed in requirements.txt

# File System Expectations

- The app expects a data/ directory at the project root. Ensure_dirs_and_csv() will create:
   - data/expenses.csv (if missing)
   - data/reports/
- data/categories.json is handled by ensure_categories_file() and load_categories().

# Running in Different Environments

- For local development: streamlit run app.py
- For deployment on a Streamlit-compatible host:
   - Ensure data/ is writable, or adjust paths accordingly.
   - Review any platform-specific file permission issues.

# 4. User Interaction & Code Flow
## 4.1 High-Level User Flow

1. User opens the app (streamlit run app.py).
2. The sidebar allows navigation between:
   - Dashboard
   - Add Expense
   - View & Filter
   - Summaries
   - Edit Entry
   - Delete
   - Export
   - Categories
3. Each “page” is rendered by a dedicated page_* function.
4. User actions (adding, editing, deleting, exporting) are handled immediately and persisted to disk.

## 4.2 Key Modules and Functions

All core logic is in app.py. Important parts:
Data & Config Utilities
- ensure_dirs_and_csv()
     - Creates data/ and data/reports/ and initializes expenses.csv if needed.
- load_df() -> pd.DataFrame
     - Reads expenses.csv, normalizes columns and types.
- save_df(df: pd.DataFrame) -> None
     - Writes DataFrame back to expenses.csv, ensuring consistent schema.
- ensure_categories_file(), load_categories(), save_categories()
     - Manage JSON-based category list.
- filter_df(...) -> pd.DataFrame
     - Core filter logic used by the View & Filter page and re-usable elsewhere.
- export_csv_bytes(df: pd.DataFrame) -> bytes
     - Utility to create CSV bytes for Streamlit download buttons.

# Page Functions (UI)

Each page is a separate function. They are called from main() based on the sidebar selection.
- page_dashboard()
     - Loads all expenses.
     - Shows metrics (st.metric) for total, entries, start, and end dates.
     - Builds category breakdown with a table + Altair bar chart.
     - Builds monthly spending trend via Altair line chart.
     - Displays monthly budget warnings using CATEGORY_BUDGETS.
- page_add()
     - Uses a Streamlit form for date, amount, category, description.
     - Uses st.session_state["amount_input"] + quick buttons +5, +10, +20.
     - Adds new row to DataFrame and saves using save_df().
- page_view_filter()
     - Combines categories from JSON and CSV.
     - Provides filters: category, date range, keyword.
     - Applies filter_df() and stores the result in st.session_state["last_view"].
     - Provides a CSV export of the filtered view.
- page_summaries()
     - Tabbed view with three summary tables:
          - By Category (bar chart)
          - By Date (line chart)
          - By Month (line chart)
     - Mainly uses groupby operations on the global DataFrame.
- page_edit()
     - Provides optional filters (month, category) for large datasets.
     - Lets user select a specific entry via labeled dropdown.
     - Updates the selected row and saves via save_df().
- page_delete()
     - Allows deletion of a specific entry (with confirmation).
     - Also provides “Undo last add” (delete last row).
- page_export()
     - Allows downloading either the current filtered view or the full dataset.
- page_categories()
     - Simple page to add or delete categories from categories.json.

# Entry Point

- main()
     - Sets Streamlit page config.
     - Builds the sidebar radio menu.
     - Calls the appropriate page_* function based on the selected page.

# 5. Known Issues

## Minor Issues
- Large datasets
     - Dropdowns on the Edit and Delete pages may become unwieldy if there are hundreds or thousands of entries.
     - Workaround: use filters on the Edit page to narrow the selection.
- Category color consistency in charts
     - Altair auto-assigns colors; the same category may not always have the same color across all charts if charts are generated independently.

## Major Issues
- None currently known that cause immediate crashes under normal usage.

## Computational Efficiency
- Current design is optimized for small to medium personal datasets.
- For very large CSVs (tens of thousands of rows or more):
     - Loading and filtering the entire DataFrame on each rerun may become slow.
     - Potential improvement: caching (st.cache_data) or using a database.

# 6. Future Work

Potential improvements and extensions:
- Authentication & multi-user support
     - Add user accounts and separate datasets per user.
- Richer budgeting system
     - Monthly budget configuration via the UI instead of a hardcoded dictionary.
     - Alerts or emails when budgets are exceeded.
- Improved performance for large datasets
     - Use st.cache_data() for heavy operations.
     - Migrate from CSV to SQLite or another lightweight database.
- More advanced charts
     - Custom Altair themes, interactive filtering inside charts, tooltips, etc.
- Internationalization
     - Support different date formats and currencies.

# 7. Ongoing Development / Maintenance

If this project is extended in the future, consider:
- Adding basic unit tests for:
     - load_df, save_df, filter_df
     - Category file handling
- Keeping a consistent style for:
     - Docstrings (Google-style or another chosen convention)
     - Section headers and comments
- Using feature branches and pull requests for major changes.
- Updating requirements.txt when adding new libraries



