# (Expense Tracker, Version 2 – Streamlit Edition)
# This version upgrades the original CLI-based Expense Tracker to an interactive web application using the Streamlit framework.
# Data Handling:
# All expense data is stored in data/expenses.csv.
# pandas is used for reading, writing, filtering, and summarizing the data.
# Technical Details:
# Streamlit widgets (st.date_input, st.number_input, st.text_input, etc.)
# replace CLI input() prompts for a graphical interface.
# Uses st.session_state to store temporary filters and recent views.
# All pandas operations (load_df, save_df, groupby summaries) reused from Version 1.
# Run the app:
# streamlit run app.py


import os
import io
import datetime as dt
import pandas as pd
import streamlit as st

# ---------------- Paths / constants ----------------
CSV_DIR = "data"
REPORTS_DIR = os.path.join(CSV_DIR, "reports")
CSV = os.path.join(CSV_DIR, "expenses.csv")
DF_COLS = ["Date", "Amount", "Category", "Description"]

# ---------------- Bootstrap ----------------
def ensure_dirs_and_csv() -> None:
    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if not os.path.exists(CSV) or os.path.getsize(CSV) == 0:
        pd.DataFrame(columns=DF_COLS).to_csv(CSV, index=False)

def load_df() -> pd.DataFrame:
    ensure_dirs_and_csv()
    if os.path.getsize(CSV) == 0:
        return pd.DataFrame(columns=DF_COLS)
    df = pd.read_csv(CSV, dtype=str)
    df = df.reindex(columns=DF_COLS)
    # normalize
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0).round(2)
    df["Category"] = df["Category"].fillna("").astype(str)
    df["Description"] = df["Description"].fillna("").astype(str)
    return df

def save_df(df: pd.DataFrame) -> None:
    out = df.copy()
    out = out.reindex(columns=DF_COLS)
    out["Amount"] = pd.to_numeric(out["Amount"], errors="coerce").fillna(0.0).round(2)
    out.to_csv(CSV, index=False)

# --------------- Helpers Functions ----------------
def format_option_label(row: pd.Series, idx: int) -> str:
    date = str(row.get("Date", ""))
    amt  = float(row.get("Amount", 0.0))
    cat  = str(row.get("Category", ""))
    desc = str(row.get("Description", ""))
    if len(desc) > 40:
        desc = desc[:37] + "..."
    return f"[{idx}] {date} | ${amt:.2f} | {cat} | {desc}"

def filter_df(df: pd.DataFrame, category: str | None, start: dt.date | None, end: dt.date | None, text: str | None) -> pd.DataFrame:
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
        blob = df.astype(str).apply(lambda row: " ".join(row.values).lower(), axis=1)
        mask &= blob.str.contains(text.lower(), na=False)

    return df[mask]

def df_date_range(df: pd.DataFrame) -> str:
    if df.empty:
        return "—"
    dmin = df["Date"].min()
    dmax = df["Date"].max()
    return f"{dmin} → {dmax}"

def export_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

# --------------- UI Pages ----------------
def page_dashboard():
    st.header("📊 Dashboard")

    df = load_df()
    if df.empty:
        st.info("No expenses yet. Use **Add Expense** to create your first entry.")
        return

    # Quick stats row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Expenses", f"${df['Amount'].sum():.2f}")
    with c2:
        st.metric("Entries", f"{len(df)}")
    with c3:
        st.metric("Date Range", df_date_range(df))

    st.divider()

    # Recent expenses
    st.subheader("Recent Expenses")
    st.dataframe(df.tail(10).reset_index(drop=True), use_container_width=True)

    # Category breakdown (table + bar)
    st.subheader("Category Breakdown")
    cat_tbl = df.groupby("Category", dropna=False)["Amount"].sum().sort_values(ascending=False).reset_index()
    st.dataframe(cat_tbl, use_container_width=True)
    st.bar_chart(cat_tbl.set_index("Category"))

    # Monthly trend
    st.subheader("Monthly Spending Trend")
    # derive YYYY-MM
    months = df.copy()
    months["Month"] = months["Date"].str.slice(0, 7)
    month_tbl = months.groupby("Month", dropna=False)["Amount"].sum().reset_index()
    st.line_chart(month_tbl.set_index("Month"))

def page_add():
    st.header("➕ Add Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        d = st.date_input("Date", value=dt.date.today())
        amt = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
        cat = st.text_input("Category (e.g., Food, Transport)", value="General")
        desc = st.text_input("Description", value="")
        submitted = st.form_submit_button("Save")

    if submitted:
        cat_clean = (cat or "General").strip().title()
        if not cat_clean:
            st.error("Category cannot be blank.")
            return
        df = load_df()
        new_row = {"Date": d.isoformat(), "Amount": float(amt), "Category": cat_clean, "Description": desc.strip()}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_df(df)
        st.success("Saved.")
        st.rerun()

def page_view_filter():
    st.header("👁️ View & Filter")

    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    with st.expander("Filters", expanded=True):
        # Category list
        categories = ["All"] + sorted([c for c in df["Category"].dropna().unique() if str(c).strip() != ""])
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            cat = st.selectbox("Category", options=categories, index=0)
        with col2:
            start = st.date_input("Start date", value=None)
        with col3:
            end = st.date_input("End date", value=None)

        text = st.text_input("Keyword search (searches all fields)", value="")
        apply_btn = st.button("Apply Filters")

    if apply_btn or "last_view" not in st.session_state:
        filtered = filter_df(df, category=cat, start=start if start else None, end=end if end else None, text=text if text else None)
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
        mime="text/csv"
    )

def page_summaries():
    st.header("📈 Summaries")
    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    tabs = st.tabs(["By Category", "By Date", "By Month"])

    # By Category
    with tabs[0]:
        tbl = df.groupby("Category", dropna=False)["Amount"].sum().reset_index(name="Total").sort_values("Total", ascending=False)
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            chart_df = tbl.set_index("Category")
            st.bar_chart(chart_df)

    # By Date
    with tabs[1]:
        tbl = df.groupby("Date", dropna=False)["Amount"].sum().reset_index(name="Total").sort_values("Date")
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            chart_df = tbl.set_index("Date")
            st.line_chart(chart_df)

    # By Month
    with tabs[2]:
        m = df.copy()
        m["Month"] = m["Date"].str.slice(0, 7)
        tbl = m.groupby("Month", dropna=False)["Amount"].sum().reset_index(name="Total").sort_values("Month")
        st.dataframe(tbl, use_container_width=True)
        if not tbl.empty:
            chart_df = tbl.set_index("Month")
            st.line_chart(chart_df)

def page_edit():
    st.header("✏️ Edit Entry")
    df = load_df()
    if df.empty:
        st.info("No expenses to edit.")
        return

    # Choose record
    options = [format_option_label(df.iloc[i], i) for i in range(len(df))]
    choice = st.selectbox("Select an entry to edit", options=options)
    idx = int(choice.split("]")[0].lstrip("[")) if choice else None
    row = df.iloc[idx] if idx is not None else None

    if row is not None:
        with st.form("edit_form"):
            d = st.date_input("Date", value=dt.date.fromisoformat(str(row["Date"]) or dt.date.today().isoformat()))
            amt = st.number_input("Amount", min_value=0.0, step=0.01, value=float(row["Amount"]), format="%.2f")
            cat = st.text_input("Category", value=str(row["Category"] or "General"))
            desc = st.text_input("Description", value=str(row["Description"] or ""))
            submitted = st.form_submit_button("Update")

        if submitted:
            cat_clean = cat.strip()
            if not cat_clean:
                st.error("Category cannot be blank.")
                return
            df.iloc[idx] = [d.isoformat(), float(amt), cat_clean.title(), desc.strip()]
            save_df(df)
            st.success("Updated.")
            st.rerun()

def page_delete():
    st.header("🗑️ Delete")
    df = load_df()
    if df.empty:
        st.info("No expenses to delete.")
        return

    # Delete by index
    st.subheader("Delete by Index")
    options = [format_option_label(df.iloc[i], i) for i in range(len(df))]
    choice = st.selectbox("Select an entry to delete", options=options, key="delete_select")
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
    st.subheader("Delete Last Entry (Undo)")
    if st.button("Delete last row"):
        if not df.empty:
            last = df.iloc[-1].to_dict()
            df = df.iloc[:-1].reset_index(drop=True)
            save_df(df)
            st.success(f"Deleted last entry: {last}")
            st.rerun()
        else:
            st.info("No expenses to delete.")

def page_export():
    st.header("📤 Export")
    df = load_df()
    if df.empty:
        st.info("No expenses yet.")
        return

    st.write("Download either the **current filtered view** (from the View page) or the **entire dataset**.")
    filtered = st.session_state.get("last_view", pd.DataFrame(columns=DF_COLS))

    col1, col2 = st.columns(2)
    with col1:
        st.write("Current View")
        if filtered.empty:
            st.info("No filtered view available yet. Go to **View & Filter** and apply filters.")
        else:
            st.download_button(
                label="⬇️ Download current view as CSV",
                data=export_csv_bytes(filtered),
                file_name=f"expenses_view_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    with col2:
        st.write("All Data")
        st.download_button(
            label="⬇️ Download ALL data as CSV",
            data=export_csv_bytes(df),
            file_name=f"expenses_all_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# --------------- App Layout ---------------
def main():
    st.set_page_config(page_title="Expense Tracker", page_icon="💵", layout="wide")
    st.title("💵 Expense Tracker")

    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            options=["Dashboard", "Add Expense", "View & Filter", "Summaries", "Edit Entry", "Delete", "Export"],
            index=0
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

if __name__ == "__main__":
    main()
