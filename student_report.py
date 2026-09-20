import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

st.set_page_config(page_title="Multi-School Management System", page_icon="🏫", layout="wide")

# ---------------------------------------------------------
# SECURITY FUNCTION (PASSWORD HASHING)
# ---------------------------------------------------------
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# ---------------------------------------------------------
# DATABASE INITIALIZATION (DATA SAFE SETUP)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("multi_school_system.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Schools Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            school_id TEXT PRIMARY KEY,
            school_name TEXT NOT NULL,
            address TEXT,
            principal_name TEXT,
            staff_count INTEGER,
            password TEXT NOT NULL
        )
    """)

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            school_id TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    
    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            school_id TEXT,
            name TEXT, student_class TEXT, roll_no TEXT, dob TEXT,
            address TEXT, phone TEXT, total_fee REAL DEFAULT 0, paid_fee REAL DEFAULT 0
        )
    """)

    # Teachers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            school_id TEXT,
            name TEXT, class_teacher TEXT, dob TEXT, phone TEXT
        )
    """)

    # Marks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            student_id TEXT, school_id TEXT, exam_type TEXT, subject TEXT, marks_obtained REAL, max_marks REAL
        )
    """)

    # Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            student_id TEXT, school_id TEXT, date TEXT, status TEXT
        )
    """)

    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['school_id'] = None
    st.session_state['role'] = None
    st.session_state['name'] = None

# ---------------------------------------------------------
# LANDING & LOGIN PAGE
# ---------------------------------------------------------
if not st.session_state['logged_in']:
    st.title("🏫 Multi-School Portal & Management System")
    
    page = st.sidebar.radio("Navigation", ["🔐 Login (School/Staff/Student)", "📝 Register New School"])

    # --- NEW SCHOOL REGISTRATION ---
    if page == "📝 Register New School":
        st.subheader("📝 Register Your School On Platform")
        with st.form("register_school_form"):
            col1, col2 = st.columns(2)
            with col1:
                s_code = st.text_input("Assign School Code / School ID* (Unique)").strip()
                s_name = st.text_input("School Full Name*")
                s_address = st.text_area("School Address")
            with col2:
                p_name = st.text_input("Principal / Director Name*")
                s_staff = st.number_input("Approximate Staff Count", min_value=1, step=1)
                s_password = st.text_input("Set Principal/Director Account Password*", type="password")

            submit_school = st.form_submit_button("Register School")

            if submit_school:
                if not s_code or not s_name or not p_name or not s_password:
                    st.error("Please fill all compulsory fields marked with *")
                else:
                    try:
                        hashed_pass = make_hashes(s_password)
                        # Register School Info
                        cursor.execute("INSERT INTO schools VALUES (?, ?, ?, ?, ?, ?)", 
                                       (s_code, s_name, s_address, p_name, s_staff, hashed_pass))
                        # Auto-create Director Account
                        director_id = f"{s_code}_director"
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, 'Director', ?)", 
                                       (director_id, s_code, hashed_pass, p_name))
                        conn.commit()
                        st.success(f"✅ School '{s_name}' registered successfully! Your Director Login ID is: `{director_id}`")
                    except sqlite3.IntegrityError:
                        st.error(f"❌ School Code '{s_code}' is already registered. Please choose a unique School ID.")

    # --- LOGIN PAGE ---
    elif page == "🔐 Login (School/Staff/Student)":
        st.subheader("🔑 Sign In To Your Portal")
        login_type = st.radio("Select Login Mode", ["Principal / Admin / Teacher", "🎓 Direct Student ID Login"])

        if login_type == "Principal / Admin / Teacher":
            with st.form("staff_login"):
                school_id = st.text_input("Enter School ID / Code")
                user_id = st.text_input("User ID (Director/Admin/Teacher ID)")
                password = st.text_input("Password", type="password")
                btn = st.form_submit_button("Login")

                if btn:
                    cursor.execute("""
                        SELECT user_id, school_id, password, role, name FROM users 
                        WHERE user_id = ? AND school_id = ?
                    """, (user_id, school_id))
                    user = cursor.fetchone()
                    if user and check_hashes(password, user[2]):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user[0]
                        st.session_state['school_id'] = user[1]
                        st.session_state['role'] = user[3]
                        st.session_state['name'] = user[4]
                        st.success(f"Welcome {user[4]}!")
                        st.rerun()
                    else:
                        st.error("Invalid School ID, User ID, or Password!")

        elif login_type == "🎓 Direct Student ID Login":
            with st.form("student_login"):
                student_id = st.text_input("Enter Student ID")
                password = st.text_input("Password", type="password")
                btn = st.form_submit_button("Student Login")

                if btn:
                    cursor.execute("""
                        SELECT user_id, school_id, password, role, name FROM users 
                        WHERE user_id = ? AND role = 'Student'
                    """, (student_id,))
                    user = cursor.fetchone()
                    if user and check_hashes(password, user[2]):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user[0]
                        st.session_state['school_id'] = user[1]
                        st.session_state['role'] = user[3]
                        st.session_state['name'] = user[4]
                        st.success(f"Welcome {user[4]}!")
                        st.rerun()
                    else:
                        st.error("Invalid Student ID or Password!")

else:
    # ---------------------------------------------------------
    # LOGGED IN DASHBOARDS
    # ---------------------------------------------------------
    sid = st.session_state['school_id']
    role = st.session_state['role']

    cursor.execute("SELECT school_name FROM schools WHERE school_id = ?", (sid,))
    s_info = cursor.fetchone()
    school_name_display = s_info[0] if s_info else "School Portal"

    st.sidebar.title(f"🏫 {school_name_display}")
    st.sidebar.write(f"👤 **Name:** {st.session_state['name']}")
    st.sidebar.write(f"📌 **Role:** {role}")
    st.sidebar.write(f"🔑 **School Code:** {sid}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # 1. DIRECTOR / PRINCIPAL PANEL
    if role == "Director":
        st.title(f"👑 Principal / Director Dashboard ({school_name_display})")
        menu = ["School Details & Profile", "Create Admin Accounts", "Manage System Users", "Full Overview"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "School Details & Profile":
            st.subheader("🏫 Registered School Profile")
            s_data = pd.read_sql_query(f"SELECT school_id, school_name, address, principal_name, staff_count FROM schools WHERE school_id = '{sid}'", conn)
            st.dataframe(s_data, use_container_width=True)

        elif choice == "Create Admin Accounts":
            st.subheader("➕ Create Admin Account for School")
            with st.form("create_admin"):
                admin_id = st.text_input("Admin ID")
                admin_name = st.text_input("Admin Name")
                admin_pass = st.text_input("Password", type="password")
                if st.form_submit_button("Create Admin"):
                    try:
                        hashed_pass = make_hashes(admin_pass)
                        cursor.execute("INSERT INTO users VALUES (?, ?, ?, 'Admin', ?)", 
                                       (admin_id, sid, hashed_pass, admin_name))
                        conn.commit()
                        st.success("Admin Created Successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Admin ID already exists!")

        elif choice == "Manage System Users":
            st.subheader("👥 System Accounts")
            users_df = pd.read_sql_query(f"SELECT user_id, role, name FROM users WHERE school_id = '{sid}'", conn)
            st.dataframe(users_df, use_container_width=True)

        elif choice == "Full Overview":
            st.subheader("📊 School Summary")
            col1, col2 = st.columns(2)
            col1.metric("Total Registered Students", pd.read_sql_query(f"SELECT COUNT(*) FROM students WHERE school_id = '{sid}'", conn).iloc[0,0])
            col2.metric("Total Teachers", pd.read_sql_query(f"SELECT COUNT(*) FROM teachers WHERE school_id = '{sid}'", conn).iloc[0,0])

    # 2. SCHOOL ADMIN PANEL
    elif role == "Admin":
        st.title("🛠️ School Admin Dashboard")
        menu = ["Add Student", "Add Teacher", "View All Records"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Add Student":
            st.subheader("➕ Add New Student")
            with st.form("add_student"):
                s_id = st.text_input("Student ID (Login ID)")
                s_pass = st.text_input("Assign Password")
                s_name = st.text_input("Student Name")
                s_class = st.text_input("Class")
                s_roll = st.text_input("Roll Number")
                s_phone = st.text_input("Phone Number")
                total_fee = st.number_input("Total Fee Amount", min_value=0.0)
                if st.form_submit_button("Save Student"):
                    try:
                        hashed_pass = make_hashes(s_pass)
                        cursor.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,0)", 
                                       (s_id, sid, s_name, s_class, s_roll, "", "", s_phone, total_fee))
                        cursor.execute("INSERT INTO users VALUES (?,?,?,'Student',?)", 
                                       (s_id, sid, hashed_pass, s_name))
                        conn.commit()
                        st.success("Student Added and Account Created!")
                    except sqlite3.IntegrityError:
                        st.error("Student ID Already Exists!")

        elif choice == "Add Teacher":
            st.subheader("➕ Add New Teacher")
            with st.form("add_teacher"):
                t_id = st.text_input("Teacher ID (Login ID)")
                t_pass = st.text_input("Assign Password")
                t_name = st.text_input("Teacher Name")
                t_class = st.text_input("Assigned Class Teacher Of")
                t_phone = st.text_input("Phone Number")
                if st.form_submit_button("Save Teacher"):
                    try:
                        hashed_pass = make_hashes(t_pass)
                        cursor.execute("INSERT INTO teachers VALUES (?,?,?,?,?,?)", 
                                       (t_id, sid, t_name, t_class, "", t_phone))
                        cursor.execute("INSERT INTO users VALUES (?,?,?,'Teacher',?)", 
                                       (t_id, sid, hashed_pass, t_name))
                        conn.commit()
                        st.success("Teacher Account Created!")
                    except sqlite3.IntegrityError:
                        st.error("Teacher ID Already Exists!")

        elif choice == "View All Records":
            st.subheader("📋 Students Directory")
            st.dataframe(pd.read_sql_query(f"SELECT * FROM students WHERE school_id = '{sid}'", conn), use_container_width=True)

    # 3. TEACHER PANEL
    elif role == "Teacher":
        st.title("👩‍🏫 Teacher Side Dashboard")
        menu = ["Mark Attendance", "Upload Exam / Test Marks"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Mark Attendance":
            st.subheader("📝 Daily Attendance Marker")
            s_df = pd.read_sql_query(f"SELECT student_id, name, student_class FROM students WHERE school_id = '{sid}'", conn)
            if not s_df.empty:
                s_id = st.selectbox("Select Student", s_df['student_id'].tolist())
                status = st.radio("Status", ["Present", "Absent"])
                date_str = str(datetime.now().date())
                if st.button("Mark Attendance"):
                    cursor.execute("INSERT INTO attendance VALUES (?, ?, ?, ?)", (s_id, sid, date_str, status))
                    conn.commit()
                    st.success(f"Attendance marked as {status} for {date_str}!")

        elif choice == "Upload Exam / Test Marks":
            st.subheader("🎯 Upload Student Marks")
            s_df = pd.read_sql_query(f"SELECT student_id, name FROM students WHERE school_id = '{sid}'", conn)
            if not s_df.empty:
                s_id = st.selectbox("Select Student", s_df['student_id'].tolist())
                exam = st.selectbox("Exam Type", ["Class Test", "Mid Term Exam", "Final Exam"])
                sub = st.text_input("Subject")
                obtained = st.number_input("Marks Obtained", min_value=0.0)
                max_m = st.number_input("Max Marks", min_value=1.0, value=100.0)
                if st.button("Submit Marks"):
                    cursor.execute("INSERT INTO marks VALUES (?,?,?,?,?,?)", (s_id, sid, exam, sub, obtained, max_m))
                    conn.commit()
                    st.success("Marks Uploaded!")

    # 4. STUDENT PORTAL
    elif role == "Student":
        st.title("🎓 Student Portal")
        u_id = st.session_state['user_id']
        
        tab1, tab2, tab3 = st.tabs(["👤 Profile & Details", "📊 Marks & Performance", "📅 Attendance Report"])
        
        with tab1:
            st.subheader("Student Profile")
            profile = pd.read_sql_query(f"SELECT * FROM students WHERE student_id = '{u_id}'", conn)
            st.dataframe(profile, use_container_width=True)
            
        with tab2:
            st.subheader("Exam & Test Marks")
            marks = pd.read_sql_query(f"SELECT exam_type, subject, marks_obtained, max_marks FROM marks WHERE student_id = '{u_id}'", conn)
            st.dataframe(marks, use_container_width=True)

        with tab3:
            st.subheader("Attendance History")
            att = pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id = '{u_id}'", conn)
            st.dataframe(att, use_container_width=True)
    
