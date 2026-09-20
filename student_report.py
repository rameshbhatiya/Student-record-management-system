import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="School Management System", page_icon="🏫", layout="wide")

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("school_system.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Users Table (For Role-based Auth)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    
    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT, student_class TEXT, roll_no TEXT, dob TEXT,
            address TEXT, phone TEXT, total_fee REAL DEFAULT 0, paid_fee REAL DEFAULT 0
        )
    """)

    # Teachers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            name TEXT, class_teacher TEXT, dob TEXT, phone TEXT
        )
    """)

    # Marks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            student_id TEXT, exam_type TEXT, subject TEXT, marks_obtained REAL, max_marks REAL
        )
    """)

    # Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            student_id TEXT, date TEXT, status TEXT
        )
    """)

    # Default Developer Account (Principal/Director)
    cursor.execute("SELECT * FROM users WHERE user_id = 'director'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('director', 'admin123', 'Director', 'School Principal/Director')")

    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# ---------------------------------------------------------
# AUTHENTICATION SESSION STATE
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['role'] = None
    st.session_state['name'] = None

# ---------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------
if not st.session_state['logged_in']:
    st.title("🏫 School Portal Login")
    st.markdown("Enter your credentials according to your assigned Role ID (Student / Teacher / Admin / Director)")
    
    with st.form("login_form"):
        user_id = st.text_input("User ID / School ID")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            cursor.execute("SELECT user_id, password, role, name FROM users WHERE user_id = ? AND password = ?", (user_id, password))
            user = cursor.fetchone()
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['role'] = user[2]
                st.session_state['name'] = user[3]
                st.success(f"Welcome {user[3]} ({user[2]})!")
                st.rerun()
            else:
                st.error("Invalid User ID or Password!")

else:
    # ---------------------------------------------------------
    # LOGGED IN NAVBAR & LOGOUT
    # ---------------------------------------------------------
    st.sidebar.title(f"👤 {st.session_state['name']}")
    st.sidebar.write(f"**Role:** {st.session_state['role']}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    role = st.session_state['role']

    # ---------------------------------------------------------
    # 1. DIRECTOR / PRINCIPAL PANEL
    # ---------------------------------------------------------
    if role == "Director":
        st.title("👑 Principal / Director Dashboard")
        menu = ["Create Admin Accounts", "Manage System Users", "Full School Overview"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Create Admin Accounts":
            st.subheader("➕ Create Admin Account")
            with st.form("create_admin"):
                admin_id = st.text_input("Admin ID")
                admin_name = st.text_input("Admin Name")
                admin_pass = st.text_input("Password", type="password")
                if st.form_submit_button("Create Admin"):
                    try:
                        cursor.execute("INSERT INTO users VALUES (?, ?, 'Admin', ?)", (admin_id, admin_pass, admin_name))
                        conn.commit()
                        st.success("Admin Created Successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Admin ID already exists!")

        elif choice == "Manage System Users":
            st.subheader("👥 System Accounts")
            users_df = pd.read_sql_query("SELECT user_id, role, name FROM users", conn)
            st.dataframe(users_df, use_container_width=True)

        elif choice == "Full School Overview":
            st.subheader("📊 Complete School Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Students", pd.read_sql_query("SELECT COUNT(*) FROM students", conn).iloc[0,0])
            col2.metric("Total Teachers", pd.read_sql_query("SELECT COUNT(*) FROM teachers", conn).iloc[0,0])
            col3.metric("System Accounts", pd.read_sql_query("SELECT COUNT(*) FROM users", conn).iloc[0,0])

    # ---------------------------------------------------------
    # 2. SCHOOL ADMIN PANEL
    # ---------------------------------------------------------
    elif role == "Admin":
        st.title("🛠️ School Admin Dashboard")
        menu = ["Add Student", "Add Teacher", "View All Records"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Add Student":
            st.subheader("➕ Add New Student")
            with st.form("add_student"):
                s_id = st.text_input("Student ID / Login ID")
                s_pass = st.text_input("Assign Password")
                s_name = st.text_input("Student Name")
                s_class = st.text_input("Class")
                s_roll = st.text_input("Roll Number")
                s_phone = st.text_input("Phone Number")
                total_fee = st.number_input("Total Fee Amount", min_value=0.0)
                if st.form_submit_button("Save Student"):
                    try:
                        cursor.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,0)", (s_id, s_name, s_class, s_roll, "", "", s_phone, total_fee))
                        cursor.execute("INSERT INTO users VALUES (?,?,'Student',?)", (s_id, s_pass, s_name))
                        conn.commit()
                        st.success("Student Added and Account Created!")
                    except sqlite3.IntegrityError:
                        st.error("ID Already Exists!")

        elif choice == "Add Teacher":
            st.subheader("➕ Add New Teacher")
            with st.form("add_teacher"):
                t_id = st.text_input("Teacher ID / Login ID")
                t_pass = st.text_input("Assign Password")
                t_name = st.text_input("Teacher Name")
                t_class = st.text_input("Assigned Class Teacher Of")
                t_phone = st.text_input("Phone Number")
                if st.form_submit_button("Save Teacher"):
                    try:
                        cursor.execute("INSERT INTO teachers VALUES (?,?,?,?,?)", (t_id, t_name, t_class, "", t_phone))
                        cursor.execute("INSERT INTO users VALUES (?,?,'Teacher',?)", (t_id, t_pass, t_name))
                        conn.commit()
                        st.success("Teacher Account Created!")
                    except sqlite3.IntegrityError:
                        st.error("Teacher ID Already Exists!")

        elif choice == "View All Records":
            st.subheader("📋 Students Directory")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

    # ---------------------------------------------------------
    # 3. TEACHER PANEL
    # ---------------------------------------------------------
    elif role == "Teacher":
        st.title("👩‍🏫 Teacher Side Dashboard")
        menu = ["Mark Attendance", "Upload Exam / Test Marks"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Mark Attendance":
            st.subheader("📝 Daily Attendance Marker")
            s_df = pd.read_sql_query("SELECT student_id, name, student_class FROM students", conn)
            if not s_df.empty:
                s_id = st.selectbox("Select Student", s_df['student_id'].tolist())
                status = st.radio("Status", ["Present", "Absent"])
                date_str = str(datetime.now().date())
                if st.button("Mark Attendance"):
                    cursor.execute("INSERT INTO attendance VALUES (?, ?, ?)", (s_id, date_str, status))
                    conn.commit()
                    st.success(f"Attendance marked as {status} for {date_str}!")

        elif choice == "Upload Exam / Test Marks":
            st.subheader("🎯 Upload Student Marks")
            s_df = pd.read_sql_query("SELECT student_id, name FROM students", conn)
            if not s_df.empty:
                s_id = st.selectbox("Select Student", s_df['student_id'].tolist())
                exam = st.selectbox("Exam Type", ["Class Test", "Mid Term Exam", "Final Exam"])
                sub = st.text_input("Subject")
                obtained = st.number_input("Marks Obtained", min_value=0.0)
                max_m = st.number_input("Max Marks", min_value=1.0, value=100.0)
                if st.button("Submit Marks"):
                    cursor.execute("INSERT INTO marks VALUES (?,?,?,?,?)", (s_id, exam, sub, obtained, max_m))
                    conn.commit()
                    st.success("Marks Uploaded!")

    # ---------------------------------------------------------
    # 4. STUDENT / PARENT PANEL
    # ---------------------------------------------------------
    elif role == "Student":
        st.title("🎓 Student Portal")
        s_id = st.session_state['user_id']
        
        tab1, tab2, tab3 = st.tabs(["👤 Profile & Details", "📊 Marks & Performance", "📅 Attendance Report"])
        
        with tab1:
            st.subheader("Student Profile")
            profile = pd.read_sql_query(f"SELECT * FROM students WHERE student_id = '{s_id}'", conn)
            st.dataframe(profile, use_container_width=True)
            
        with tab2:
            st.subheader("Exam & Test Marks")
            marks = pd.read_sql_query(f"SELECT exam_type, subject, marks_obtained, max_marks FROM marks WHERE student_id = '{s_id}'", conn)
            st.dataframe(marks, use_container_width=True)

        with tab3:
            st.subheader("Attendance History")
            att = pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id = '{s_id}'", conn)
            st.dataframe(att, use_container_width=True)
    
