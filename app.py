"""
Expense Tracker (Streamlit Edition)

This module implements a small personal expense tracking application with
a Streamlit-based web UI. Users can:

- Add, edit, delete, and filter expenses stored in data/expenses.csv
- Manage categories stored in data/categories.json
- View dashboards and summaries (by category, date, month)
- Export filtered or full data sets as CSV files
- See optional monthly budget warnings per category

Run the app with:

    streamlit run app.py

The main entry point is the `main()` function at the bottom of this file.
"""

import os
import io
import json
import datetime as dt
import pandas as pd
import streamlit as st
import altair as alt  # for richer charts

# ---------------- Paths / constants ----------------
CSV_DIR = "data"
REPORTS_DIR = os.path.join(CSV_DIR, "reports")
CSV = os.path.join(CSV_DIR, "expenses.csv")
DF_COLS = ["Date", "Amount", "Category", "Description"]
CATS_JSON = os.path.join(CSV_DIR, "categories.json")

DEFAULT_CATEGORIES = ["Food", "Transport", "Bills", "Groceries", "Health", "Other"]

# Optional monthly budgets per category (for warnings on dashboard)
# TODO: In the future, this could be loaded from a separate config file or edited via a UI page.
CATEGORY_BUDGETS = {
    "Food": 300.0,
    "Transport": 150.0,
    "Bills": 400.0,
    "Groceries": 250.0,
    "Health": 150.0,
    "Other": 100.0,
}


# ---------------- Bootstrap ----------------
def ensure_dirs_and_csv() -> None:
    """Ensure data folders and main CSV file exist.

    Creates the data/ and data/reports/ directories if needed and
    initializes an empty expenses.csv file with the expected columns
    if the file does not exist or is empty.
    """
    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if not os.path.exists(CSV) or os.path.getsize(CSV) == 0:
        pd.DataFrame(columns=DF_COLS).to_csv(CSV, index=False)


def load_df() -> pd.DataFrame:
    """Load all expenses from CSV into a pandas DataFrame.

    Returns:
        A DataFrame with columns: Date, Amount, Category, Description.
        If the CSV is empty or missing, an empty DataFrame is returned.
    """
    ensure_dirs_and_csv()
    if os.path.getsize(CSV) == 0:
        return pd.DataFrame(columns=DF_COLS)
    df = pd.read_csv(CSV, dtype=str)
    df = df.reindex(columns=DF_COLS)
    # Normalize numeric and text columns
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0).round(2)
    df["Category"] = df["Category"].fillna("").astype(str)
    df["Description"] = df["Description"].fillna("").astype(str)
    return df


def save_df(df: pd.DataFrame) -> None:
    """Save the given expenses DataFrame back to the CSV file.

    The function normalizes the column order and amount type before writing.

    Args:
        df: A DataFrame with at least the DF_COLS columns.
    """
    out = df.copy()
    out = out.reindex(columns=DF_COLS)
    out["Amount"] = pd.to_numeric(out["Amount"], errors="coerce").fillna(0.0).round(2)
    out.to_csv(CSV, index=False)


# --------------- Categories Config ----------------
def ensure_categories_file() -> None:
    """Ensure the categories JSON file exists.

    If the JSON file does not exist, create it with DEFAULT_CATEGORIES.
    """
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CATS_JSON):
        with open(CATS_JSON, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CATEGORIES, f)


def load_categories() -> list[str]:
    """Load categories from JSON, normalize casing, remove duplicates.

    Returns:
        A sorted list of unique category names in title case.
    """
    ensure_categories_file()
    with open(CATS_JSON, "r", encoding="utf-8") as f:
        cats = json.load(f)
    norm = sorted({c.strip().title() for c in cats if c and c.strip()})
    return norm


def save_categories(categories: list[str]) -> None:
    """Save categories back to JSON with normalized casing.

    Args:
        categories: A list of category names to be saved.
    """
    norm = sorted({c.strip().title() for c in categories if c and c.strip()})
    with open(CATS_JSON, "w", encoding="utf-8") as f:
        json.dump(norm, f)


# --------------- Helper Functions ----------------
def format_option_label(row: pd.Series, idx: int) -> str:
    """Format a single row as a human-readable label for dropdowns.

    Args:
        row: A pandas Series representing one expense row.
        idx: The original index of the row (used as an identifier).

    Returns:
        A string like: "[12] 2025-01-01 | $10.00 | Food | Short description..."
    """
    date = str(row.get("Date", ""))
    amt = float(row.get("Amount", 0.0))
    cat = str(row.get("Category", ""))
    desc = str(row.get("Description", ""))
    if len(desc) > 40:
        desc = desc[:37] + "..."
    return f"[{idx}] {date} | ${amt:.2f} | {cat} | {desc}"


def filter_df(
    df: pd.DataFrame,
    category: str | None,
    start: dt.date | None,
    end: dt.date | None,
    text: str | None,
) -> pd.DataFrame:
    """Filter the expenses DataFrame by category, date range, and text.

    Args:
        df: Full expenses DataFrame.
        category: Category name to filter by, or 'All'/None for no filter.
        start: Optional start date (inclusive).
        end: Optional end date (inclusive).
        text: Optional substring to search across all fields (case-insensitive).

    Returns:
        A filtered DataFrame containing only matching rows.
    """
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)

    if category and category != "All":
        mask &= df["Category"].str.lower().eq(category.lower())

    if start:
        mask &= df["Date"] >= start.isoformat()
    if end:
        mask &= df["Date"] <= end.isoformat()

    if text:
        # GOTCHA: This text search converts the whole row to a single string,
        # which is simple but can be slow for very large datasets.
        blob = df.astype(str).apply(lambda row: " ".join(row.values).lower(), axis=1)
        mask &= blob.str.contains(text.lower(), na=False)

    return df[mask]


def export_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes for Streamlit download buttons.

    Args:
        df: The DataFrame to export.

    Returns:
        Bytes containing the CSV representation of the DataFrame.
    """
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


# --------------- UI Pages ----------------
def page_dashboard() -> None:
    """Render the main dashboard page.

    Shows:
        - Total amount and number of entries
        - Start and end date of the data
        - Recent expenses table
        - Category breakdown (table + bar chart)
        - Monthly spending trend (line chart)
        - Monthly budget warnings for the current month
    """
    st.header("📊 Dashboard")

    df = load_df()
    if df.empty:
        st.info("No expenses yet. Use **Add Expense** to create your first entry.")
        return

    # Quick stats row (split date range into Start / End)
    dmin = df["Date"].min()
    dmax = df["Date"].max()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total", f"${df['Amount'].sum():.2f}")
    with c2:
        st.metric("Entries", f"{len(df)}")
    with c3:
        st.metric("Start", dmin if pd.notna(dmin) else "—")
    with c4:
        st.metric("End", dmax if pd.notna(dmax) else "—")

    st.divider()

    # Recent expenses
    st.subheader("Recent Expenses")
    st.dataframe(df.tail(10).reset_index(drop=True), use_container_width=True)

    # Category breakdown (table + Altair bar chart)
    st.subheader("Category Breakdown")
    cat_tbl = (
        df.groupby("Category", dropna=False)["Amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(cat_tbl, use_container_width=True)

    if not cat_tbl.empty:
        cat_chart = (
            alt.Chart(cat_tbl)
            .mark_bar()
            .encode(
                x=alt.X("Category:N", sort="-y"),
                y=alt.Y("Amount:Q"),
                color="Category:N",
                tooltip=["Category", "Amount"],
            )
            .properties(height=300)
        )
        st.altair_chart(cat_chart, use_container_width=True)

    # Monthly trend (Altair line chart)
    st.subheader("Monthly Spending Trend")
    months = df.copy()
    months["Month"] = months["Date"].str.slice(0, 7)
    month_tbl = (
        months.groupby("Month", dropna=False)["Amount"]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    if not month_tbl.empty:
        month_chart = (
            alt.Chart(month_tbl)
            .mark_line(point=True)
            .encode(
                x="Month:N",
                y="Amount:Q",
                tooltip=["Month", "Amount"],
            )
            .properties(height=300)
        )
        st.altair_chart(month_chart, use_container_width=True)
    else:
        st.info("No monthly data yet.")

    st.divider()

    # Monthly budget warnings (for current month)
    st.subheader("Monthly Budget Warnings (this month)")
    current_month = dt.date.today().isoformat()[:7]
    this_month = df[df["Date"].str.startswith(current_month)]

    if this_month.empty:
        st.info("No expenses recorded for this month yet.")
    else:
        totals = this_month.groupby("Category")["Amount"].sum()
        any_warning = False
        for cat, total in totals.items():
            budget = CATEGORY_BUDGETS.get(cat)
            if not budget:
                continue  # no budget defined for this category
            any_warning = True
            if total >= budget:
                st.error(f"{cat}: ${total:.2f} / ${budget:.2f} — OVER budget")
            elif total >= 0.8 * budget:
                st.warning(f"{cat}: ${total:.2f} / ${budget:.2f} — close to budget")
            else:
                st.success(f"{cat}: ${total:.2f} / ${budget:.2f} — within budget")
        if not any_warning:
            st.info("No budgets defined for the categories used this month.")


def page_add() -> None:
    """Render the Add Expense page.

    Allows the user to:
        - Pick a date
        - Enter an amount (with quick +5, +10, +20 buttons)
        - Choose or add a category
        - Enter an optional description
    """
    st.header("➕ Add Expense")

    cats = load_categories()

    # Initialize amount in session state (for quick buttons)
    if "amount_input" not in st.session_state:
        st.session_state["amount_input"] = 0.0

    # Main form
    with st.form("add_expense_form"):
        d = st.date_input("Date", value=dt.date.today())

        col_amount, col_cat = st.columns([1.2, 1.8])
        with col_amount:
            # Use session_state value (no key here!)
            amt = st.number_input(
                "Amount",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                value=float(st.session_state["amount_input"]),
            )

        with col_cat:
            col1, col2 = st.columns(2)
            with col1:
                cat_choice = st.selectbox(
                    "Category",
                    options=cats + ["(Add new...)"],
                    index=0 if cats else len(cats),
                )
            with col2:
                new_cat = st.text_input("If new, type category", value="")

        desc = st.text_input("Description", value="")
        submitted = st.form_submit_button("Save")

    # Quick-entry amount buttons (+5, +10, +20)
    st.caption("Quick amount buttons (optional):")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("+5"):
            st.session_state["amount_input"] = float(
                st.session_state.get("amount_input", 0.0)
            ) + 5
    with q2:
        if st.button("+10"):
            st.session_state["amount_input"] = float(
                st.session_state.get("amount_input", 0.0)
            ) + 10
    with q3:
        if st.button("+20"):
            st.session_state["amount_input"] = float(
                st.session_state.get("amount_input", 0.0)
            ) + 20

    # When user clicks Save
    if submitted:
        # Keep session_state in sync with what was actually submitted
        st.session_state["amount_input"] = float(amt)

        if cat_choice == "(Add new...)":
            cat_clean = new_cat.strip().title()
            if not cat_clean:
                st.error("Please type a new category name or select an existing one.")
                return
            all_cats = load_categories()
            all_cats.append(cat_clean)
            save_categories(all_cats)
        else:
            cat_clean = cat_choice.strip().title()

        df = load_df()
        new_row = {
            "Date": d.isoformat(),
            "Amount": float(amt),
            "Category": cat_clean,
            "Description": desc.strip(),
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_df(df)
        st.success("Saved.")

        # Reset amount back to 0 for next entry
        st.session_state["amount_input"] = 0.0
        st.rerun()


def page_view_filter() -> None:
    """Render the View & Filter page.

    Allows the user to:
        - Filter by category, date range, and keyword
        - View the filtered DataFrame
        - Download the filtered set as CSV
    """
    st.header("👁️ View & Filter")

    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    with st.expander("Filters", expanded=True):
        # Category list: combine categories file + what exists in data
        cats_conf = load_categories()
        cats_data = sorted(
            [
                c
                for c in df["Category"].dropna().unique()
                if str(c).strip() != ""
            ]
        )
        all_cats = sorted(set(cats_conf) | set(cats_data))

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            categories = ["All"] + all_cats
            cat = st.selectbox("Category", options=categories, index=0)
        with col2:
            start = st.date_input("Start date", value=None)
        with col3:
            end = st.date_input("End date", value=None)

        text = st.text_input("Keyword search (searches all fields)", value="")
        apply_btn = st.button("Apply Filters")

    if apply_btn or "last_view" not in st.session_state:
        filtered = filter_df(
            df,
            category=cat,
            start=start if start else None,
            end=end if end else None,
            text=text if text else None,
        )
        st.session_state["last_view"] = filtered.copy()
    else:
        filtered = st.session_state["last_view"]

    if filtered.empty:
        st.warning("No matching expenses.")
        return

    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

    st.download_button(
        label="⬇️ Download current view as CSV",
        data=export_csv_bytes(filtered),
        file_name=f"expenses_view_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


def page_summaries() -> None:
    """Render the Summaries page.

    Provides three tabs:
        - By Category: totals per category (table + bar chart)
        - By Date: totals per day (table + line chart)
        - By Month: totals per month (table + line chart)
    """
    st.header("📈 Summaries")
    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    tabs = st.tabs(["By Category", "By Date", "By Month"])

    # By Category
    with tabs[0]:
        tbl = (
            df.groupby("Category", dropna=False)["Amount"]
            .sum()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            cat_chart = (
                alt.Chart(tbl)
                .mark_bar()
                .encode(
                    x=alt.X("Category:N", sort="-y"),
                    y="Total:Q",
                    color="Category:N",
                    tooltip=["Category", "Total"],
                )
                .properties(height=300)
            )
            st.altair_chart(cat_chart, use_container_width=True)

    # By Date
    with tabs[1]:
        tbl = (
            df.groupby("Date", dropna=False)["Amount"]
            .sum()
            .reset_index(name="Total")
            .sort_values("Date")
        )
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            date_chart = (
                alt.Chart(tbl)
                .mark_line(point=True)
                .encode(
                    x="Date:N",
                    y="Total:Q",
                    tooltip=["Date", "Total"],
                )
                .properties(height=300)
            )
            st.altair_chart(date_chart, use_container_width=True)

    # By Month
    with tabs[2]:
        m = df.copy()
        m["Month"] = m["Date"].str.slice(0, 7)
        tbl = (
            m.groupby("Month", dropna=False)["Amount"]
            .sum()
            .reset_index(name="Total")
            .sort_values("Month")
        )
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            month_chart = (
                alt.Chart(tbl)
                .mark_line(point=True)
                .encode(
                    x="Month:N",
                    y="Total:Q",
                    tooltip=["Month", "Total"],
                )
                .properties(height=300)
            )
            st.altair_chart(month_chart, use_container_width=True)


def page_edit() -> None:
    """Render the Edit Entry page.

    Allows the user to:
        - Filter entries by month and category
        - Select a specific entry
        - Update date, amount, category, and description
    """
    st.header("✏️ Edit Entry")
    df = load_df()
    if df.empty:
        st.info("No expenses to edit.")
        return

    # Filters for Edit page (month + category)
    with st.expander("Filters (optional)", expanded=False):
        # Months from data
        months = sorted(df["Date"].str.slice(0, 7).dropna().unique().tolist())
        months = ["All"] + months
        month_sel = st.selectbox("Month", options=months, index=0)

        cats_conf = load_categories()
        cats_data = sorted(
            [
                c
                for c in df["Category"].dropna().unique()
                if str(c).strip() != ""
            ]
        )
        all_cats = sorted(set(cats_conf) | set(cats_data))
        categories = ["All"] + all_cats
        cat_sel = st.selectbox("Category", options=categories, index=0)

    df_filtered = df.copy()
    if month_sel != "All":
        df_filtered = df_filtered[df_filtered["Date"].str.slice(0, 7) == month_sel]
    if cat_sel != "All":
        df_filtered = df_filtered[
            df_filtered["Category"].str.lower() == cat_sel.lower()
        ]

    if df_filtered.empty:
        st.warning("No entries match the selected filters.")
        return

    # GOTCHA: For very large datasets, this dropdown might still be long.
    # Filters above help reduce the number of options.
    options = [
        format_option_label(df_filtered.loc[idx], idx) for idx in df_filtered.index
    ]
    choice = st.selectbox("Select an entry to edit", options=options)
    idx = int(choice.split("]")[0].lstrip("[")) if choice else None
    row = df.loc[idx] if idx is not None else None

    if row is not None:
        with st.form("edit_form"):
            d = st.date_input(
                "Date",
                value=dt.date.fromisoformat(
                    str(row["Date"]) or dt.date.today().isoformat()
                ),
            )
            amt = st.number_input(
                "Amount",
                min_value=0.0,
                step=1.0,
                value=float(row["Amount"]),
                format="%.2f",
            )
            cats = load_categories()
            if row["Category"] in cats:
                cat = st.selectbox(
                    "Category", options=cats, index=cats.index(row["Category"])
                )
            else:
                cat = st.selectbox("Category", options=cats, index=0)
            desc = st.text_input("Description", value=str(row["Description"] or ""))
            submitted = st.form_submit_button("Update")

        if submitted:
            cat_clean = cat.strip()
            if not cat_clean:
                st.error("Category cannot be blank.")
                return
            df.loc[idx] = [d.isoformat(), float(amt), cat_clean.title(), desc.strip()]
            save_df(df)
            st.success("Updated.")
            st.rerun()


def page_delete() -> None:
    """Render the Delete page.

    Provides:
        - Delete-by-entry (with a confirmation step)
        - Undo last added entry (delete last row)
    """
    st.header("🗑️ Delete")
    df = load_df()
    if df.empty:
        st.info("No expenses to delete.")
        return

    # Delete by index
    st.subheader("Delete by Index")
    options = [format_option_label(df.iloc[i], i) for i in range(len(df))]
    choice = st.selectbox(
        "Select an entry to delete", options=options, key="delete_select"
    )
    idx = int(choice.split("]")[0].lstrip("[")) if choice else None

    if idx is not None:
        st.warning(f"About to delete: {df.iloc[idx].to_dict()}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Delete", type="primary"):
                df = df.drop(df.index[idx]).reset_index(drop=True)
                save_df(df)
                st.success("Deleted.")
                st.rerun()
        with col2:
            st.button("Cancel")

    st.divider()
    st.subheader("Undo: delete last added entry")
    if st.button("Undo last add"):
        if not df.empty:
            last = df.iloc[-1].to_dict()
            df = df.iloc[:-1].reset_index(drop=True)
            save_df(df)
            st.success(f"Undid last entry: {last}")
            st.rerun()
        else:
            st.info("No expenses to delete.")


def page_export() -> None:
    """Render the Export page.

    Allows the user to:
        - Download the last filtered view
        - Download the full dataset
    """
    st.header("📤 Export")
    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    st.write(
        "Download either the **current filtered view** (from the View page) or the **entire dataset**."
    )
    filtered = st.session_state.get("last_view", pd.DataFrame(columns=DF_COLS))

    col1, col2 = st.columns(2)
    with col1:
        st.write("Current View")
        if filtered.empty:
            st.info(
                "No filtered view available yet. Go to **View & Filter** and apply filters."
            )
        else:
            st.download_button(
                label="⬇️ Download current view as CSV",
                data=export_csv_bytes(filtered),
                file_name=f"expenses_view_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    with col2:
        st.write("All Data")
        st.download_button(
            label="⬇️ Download ALL data as CSV",
            data=export_csv_bytes(df),
            file_name=f"expenses_all_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def page_categories() -> None:
    """Render the Categories page.

    Allows the user to:
        - View existing categories
        - Add new categories
        - Delete existing categories
    """
    st.header("🏷️ Categories")

    cats = load_categories()

    st.subheader("Existing Categories")
    if cats:
        st.write(", ".join(cats))
    else:
        st.info("No categories yet.")

    # Add category
    with st.form("add_cat_form"):
        new_cat = st.text_input("Add a new category", placeholder="e.g., Entertainment")
        submitted = st.form_submit_button("Add")
    if submitted:
        if not new_cat.strip():
            st.error("Category cannot be blank.")
        else:
            cats.append(new_cat.strip())
            save_categories(cats)
            st.success(f"Added category: {new_cat.strip().title()}")
            st.rerun()

    st.divider()

    # Delete category
    st.subheader("Delete Category")
    if cats:
        cat_to_delete = st.selectbox("Select category to delete", options=cats)
        if st.button("Delete selected category"):
            remain = [c for c in cats if c != cat_to_delete]
            save_categories(remain)
            st.success(f"Deleted category: {cat_to_delete}")
            st.rerun()
    else:
        st.info("No categories to delete.")


# --------------- App Layout ---------------
def main() -> None:
    """Main entry point for the Streamlit app.

    Sets the page configuration, renders the sidebar navigation, and
    dispatches to the appropriate page_* function based on user choice.
    """
    st.set_page_config(page_title="Expense Tracker", page_icon="💵", layout="wide")
    st.title("💵 Expense Tracker")

    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            options=[
                "Dashboard",
                "Add Expense",
                "View & Filter",
                "Summaries",
                "Edit Entry",
                "Delete",
                "Export",
                "Categories",
            ],
            index=0,
        )
        st.caption("Tip: Data persists in data/expenses.csv")

    if page == "Dashboard":
        page_dashboard()
    elif page == "Add Expense":
        page_add()
    elif page == "View & Filter":
        page_view_filter()
    elif page == "Summaries":
        page_summaries()
    elif page == "Edit Entry":
        page_edit()
    elif page == "Delete":
        page_delete()
    elif page == "Export":
        page_export()
    elif page == "Categories":
        page_categories()


if __name__ == "__main__":
    main()
