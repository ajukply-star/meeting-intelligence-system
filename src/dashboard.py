import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, date

DB_PATH = "data/meetings.db"

st.set_page_config(
    page_title="Meeting Intelligence Dashboard",
    layout="wide"
)

st.title("Meeting Intelligence Dashboard")

def get_connection():
    return sqlite3.connect(DB_PATH)


def load_action_items():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, meeting_id, task, assignee, deadline, priority, completed, completed_at
        FROM action_items
        ORDER BY deadline ASC
    """, conn)
    conn.close()
    return df


def load_meetings():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, date, summary, follow_up_needed, created_at
        FROM meetings
        ORDER BY created_at DESC
    """, conn)
    conn.close()
    return df


df_items = load_action_items()
df_meetings = load_meetings()

# ── Top metrics row ──
col1, col2, col3, col4 = st.columns(4)

total = len(df_items)
completed = df_items["completed"].sum()
overdue = df_items[
    (df_items["completed"] == 0) &
    (pd.to_datetime(df_items["deadline"], errors="coerce") < pd.Timestamp.now())
]

completion_rate = (completed / total * 100) if total > 0 else 0

col1.metric("Total meetings", len(df_meetings))
col2.metric("Total action items", total)
col3.metric("Completion rate", f"{completion_rate:.1f}%")
col4.metric("Overdue tasks", len(overdue))

st.divider()

# ── Completion rate by person ──
st.subheader("Completion rate by person")

if not df_items.empty:
    by_person = df_items.groupby("assignee").agg(
        total=("id", "count"),
        done=("completed", "sum")
    ).reset_index()
    by_person["rate"] = (by_person["done"] / by_person["total"] * 100).round(1)
    st.bar_chart(by_person.set_index("assignee")["rate"])
else:
    st.info("No action items yet. Run a meeting through the pipeline first.")

st.divider()

# ── Overdue tasks ──
st.subheader(f"Overdue tasks ({len(overdue)})")

if not overdue.empty:
    st.dataframe(
        overdue[["task", "assignee", "deadline", "priority"]],
        use_container_width=True
    )
else:
    st.success("No overdue tasks!")

st.divider()

# ── All action items with complete button ──
st.subheader("All action items")

pending = df_items[df_items["completed"] == 0]

if not pending.empty:
    for _, row in pending.iterrows():
        col_a, col_b, col_c, col_d, col_e = st.columns([4, 2, 2, 1, 1])
        col_a.write(row["task"])
        col_b.write(row["assignee"])
        col_c.write(row["deadline"])
        col_d.write(row["priority"])
        if col_e.button("Done", key=row["id"]):
            conn = get_connection()
            conn.execute(
                "UPDATE action_items SET completed=1, completed_at=? WHERE id=?",
                (datetime.now().isoformat(), row["id"])
            )
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.success("All tasks completed!")

st.divider()

# ── Recent meetings ──
st.subheader("Recent meetings")

if not df_meetings.empty:
    for _, row in df_meetings.iterrows():
        with st.expander(f"Meeting — {row['date'][:10]}"):
            st.write(row["summary"])
            if row["follow_up_needed"]:
                st.warning("Follow-up meeting needed")
else:
    st.info("No meetings recorded yet.")