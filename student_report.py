import streamlit as st
import sqlite3
import pandas as pd

# Database init
conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, course TEXT, total_fee REAL, paid_fee REAL
    )
""")
conn.commit()

st.title("🎓 Student Record Management System")

menu = ["Add Student", "View All", "Search", "Update Payment", "Delete"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Add Student":
    st.subheader("Add Student Record")
    name = st.text_input("Student Name")
    course = st.text_input("Course")
    total_fee = st.number_input("Total Fee", min_value=0.0)
    paid_fee = st.number_input("Paid Amount", min_value=0.0)
    if st.button("Save"):
        cursor.execute("INSERT INTO students (name, course, total_fee, paid_fee) VALUES (?,?,?,?)", (name, course, total_fee, paid_fee))
        conn.commit()
        st.success("Record Added!")

elif choice == "View All":
    st.subheader("All Student Records")
    df = pd.read_sql_query("SELECT *, (total_fee - paid_fee) as pending_fee FROM students", conn)
    st.dataframe(df)

elif choice == "Search":
    query = st.text_input("Search by Name or ID")
    if query:
        df = pd.read_sql_query(f"SELECT * FROM students WHERE name LIKE '%{query}%' OR id='{query}'", conn)
        st.dataframe(df)

elif choice == "Update Payment":
    sid = st.number_input("Student ID", step=1)
    amount = st.number_input("Payment Amount")
    if st.button("Update"):
        cursor.execute("UPDATE students SET paid_fee = paid_fee + ? WHERE id = ?", (amount, sid))
        conn.commit()
        st.success("Payment Updated!")

elif choice == "Delete":
    sid = st.number_input("Student ID to Delete", step=1)
    if st.button("Delete Record"):
        cursor.execute("DELETE FROM students WHERE id = ?", (sid,))
        conn.commit()
        st.warning("Record Deleted!")
