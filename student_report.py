import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import re
from datetime import datetime

st.set_page_config(page_title="Multi-School Management System", page_icon="🏫", layout="wide")

# ---------------------------------------------------------
# SECURITY & VALIDATION FUNCTIONS
# ---------------------------------------------------------
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def is_strong_password(password):
    # Minimum 6 characters, at least one letter and one number
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False, "Password must contain both letters and numbers."
    return True, ""

# ---------------------------------------------------------
# DATABASE INITIALIZATION (SAFE PRESERVATION)
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
            sr_no TEXT,
            name TEXT, student_class TEXT, roll_no TEXT, dob TEXT,
            address TEXT, phone TEXT, total_fee REAL DEFAULT 0, paid_fee REAL DEFAULT 0
        )
    """)

    # Teachers & Staff Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id TEXT PRIMARY KEY,
            school_id TEXT,
            name TEXT, role_type TEXT, class_teacher TEXT, dob TEXT, phone TEXT
        )
    """)

    # Marks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            student_id TEXT, school_id TEXT, exam_type TEXT, subject TEXT, marks_obtained REAL, max_marks REAL
        )
    """)

    # Universal Attendance Table (For Students, Teachers, Admin, Director)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            person_id TEXT, school_id TEXT, role TEXT, date TEXT, status TEXT
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
    st.title("🏫 School Portal & Management Platform")
    
    page = st.sidebar.radio("Navigation", [
        "👀 Guest Visitor Mode", 
        "🔐 Login (Portal)", 
        "📝 Register New School"
    ])

    # 1. GUEST VISITOR MODE
    if page == "👀 Guest Visitor Mode":
        st.subheader("🌐 Welcome Guest Visitor!")
        st.info("You are exploring in Guest Mode. Here is the public directory of registered schools.")
        
        schools_df = pd.read_sql_query("SELECT school_id, school_name, address, principal_name FROM schools", conn)
        if not schools_df.empty:
            st.dataframe(schools_df, use_container_width=True)
            
            st.markdown("---")
            selected_s = st.selectbox("View School Info", schools_df['school_id'].tolist())
            if selected_s:
                s_detail = pd.read_sql_query(f"SELECT * FROM schools WHERE school_id='{selected_s}'", conn)
                st.write(f"### 🏫 {s_detail.iloc[0]['school_name']}")
                st.write(f"📍 **Address:** {s_detail.iloc[0]['address']}")
                st.write(f"👨‍🏫 **Principal:** {s_detail.iloc[0]['principal_name']}")
        else:
            st.warning("No registered schools found yet.")

    # 2. REGISTER NEW SCHOOL
    elif page == "📝 Register New School":
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
                s_password = st.text_input("Set Principal/Director Password* (Min 6 chars, Letters+Numbers)", type="password")

            # Unique ID Validation Check
            if s_code:
                cursor.execute("SELECT school_id FROM schools WHERE school_id = ?", (s_code,))
                if cursor.fetchone():
                    st.error(f"⚠️ School ID '{s_code}' is ALREADY TAKEN! Please choose another code.")

            submit_school = st.form_submit_button("Register School")

            if submit_school:
                # Password Validation Check
                is_valid_pass, pass_msg = is_strong_password(s_password)
                
                cursor.execute("SELECT school_id FROM schools WHERE school_id = ?", (s_code,))
                if cursor.fetchone():
                    st.error("❌ Cannot register. School ID is already taken!")
                elif not is_valid_pass:
                    st.error(f"❌ Weak Password: {pass_msg}")
                elif not s_code or not s_name or not p_name:
                    st.error("Please fill all required fields!")
                else:
                    hashed_pass = make_hashes(s_password)
                    cursor.execute("INSERT INTO schools VALUES (?, ?, ?, ?, ?, ?)", 
                                   (s_code, s_name, s_address, p_name, s_staff, hashed_pass))
                    
                    director_id = f"{s_code}_director"
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, 'Director', ?)", 
                                   (director_id, s_code, hashed_pass, p_name))
                    conn.commit()
                    st.success(f"✅ School '{s_name}' registered successfully! Your Login ID: `{director_id}`")

    # 3. LOGIN PAGE
    elif page == "🔐 Login (Portal)":
        st.subheader("🔑 Sign In To Your Account")
        login_type = st.radio("Select Login Mode", ["School Staff / Admin / Director", "🎓 Student Direct Login"])

        if login_type == "School Staff / Admin / Director":
            with st.form("staff_login"):
                school_id = st.text_input("School ID / Code")
                user_id = st.text_input("User ID")
                password = st.text_input("Password", type="password")
                btn = st.form_submit_button("Login")

                if btn:
                    cursor.execute("SELECT user_id, school_id, password, role, name FROM users WHERE user_id = ? AND school_id = ?", (user_id, school_id))
                    user = cursor.fetchone()
                    if user and check_hashes(password, user[2]):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user[0]
                        st.session_state['school_id'] = user[1]
                        st.session_state['role'] = user[3]
                        st.session_state['name'] = user[4]
                        st.success(f"Welcome {user[4]} ({user[3]})!")
                        st.rerun()
                    else:
                        st.error("Invalid Credentials!")

        elif login_type == "🎓 Student Direct Login":
            with st.form("student_login"):
                student_id = st.text_input("Student ID (First Name + SR Number)")
                password = st.text_input("Password (DOB e.g. YYYY-MM-DD)", type="password")
                btn = st.form_submit_button("Student Login")

                if btn:
                    cursor.execute("SELECT user_id, school_id, password, role, name FROM users WHERE user_id = ? AND role = 'Student'", (student_id,))
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
                        st.error("Invalid Student ID or DOB Password!")

else:
    # ---------------------------------------------------------
    # DASHBOARDS
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

    # 1. DIRECTOR / PRINCIPAL DASHBOARD
    if role in ["Director", "Principal"]:
        st.title(f"👑 {role} Dashboard")
        menu = ["Manage Management Roles (Admin/Vice Principal)", "School Overview & Data Update", "Universal Attendance Tracker"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Manage Management Roles (Admin/Vice Principal)":
            st.subheader("➕ Create Admin / Vice Principal Accounts")
            with st.form("create_admin_form"):
                new_role = st.selectbox("Assign Role", ["Admin", "Vice Principal"])
                a_id = st.text_input("User ID")
                a_name = st.text_input("Full Name")
                a_pass = st.text_input("Assign Password (Strong)", type="password")
                
                if st.form_submit_button("Create User Account"):
                    is_valid, msg = is_strong_password(a_pass)
                    if not is_valid:
                        st.error(msg)
                    else:
                        try:
                            hashed = make_hashes(a_pass)
                            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (a_id, sid, hashed, new_role, a_name))
                            conn.commit()
                            st.success(f"{new_role} Account Created Successfully!")
                        except sqlite3.IntegrityError:
                            st.error("User ID already exists!")

        elif choice == "School Overview & Data Update":
            st.subheader("📊 System Directory & Records")
            st.dataframe(pd.read_sql_query(f"SELECT user_id, role, name FROM users WHERE school_id = '{sid}'", conn), use_container_width=True)

        elif choice == "Universal Attendance Tracker":
            st.subheader("📅 Attendance History (All Roles)")
            att_df = pd.read_sql_query(f"SELECT * FROM attendance WHERE school_id='{sid}'", conn)
            st.dataframe(att_df, use_container_width=True)

    # 2. ADMIN / VICE PRINCIPAL DASHBOARD
    elif role in ["Admin", "Vice Principal"]:
        st.title(f"🛠️ {role} Dashboard")
        menu = ["Add Student (Auto Credentials)", "Add Teacher / Staff", "Update School Data", "Mark Daily Attendance"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Add Student (Auto Credentials)":
            st.subheader("➕ Add New Student")
            st.info("Note: Student UID = First Name + SR Number | Password = Date of Birth (YYYY-MM-DD)")
            with st.form("add_student_form"):
                first_name = st.text_input("First Name*").strip()
                last_name = st.text_input("Last Name").strip()
                sr_no = st.text_input("SR Number*").strip()
                s_class = st.text_input("Class")
                s_roll = st.text_input("Roll Number")
                dob = st.date_input("Date of Birth (Password)")
                s_phone = st.text_input("Phone Number")
                total_fee = st.number_input("Total Fee Amount", min_value=0.0)

                if st.form_submit_button("Register Student"):
                    full_name = f"{first_name} {last_name}".strip()
                    auto_student_id = f"{first_name}{sr_no}"
                    dob_str = str(dob)

                    if not first_name or not sr_no:
                        st.error("First Name and SR Number are mandatory!")
                    else:
                        try:
                            hashed_pass = make_hashes(dob_str)
                            cursor.execute("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,0)", 
                                           (auto_student_id, sid, sr_no, full_name, s_class, s_roll, dob_str, "", s_phone, total_fee))
                            cursor.execute("INSERT INTO users VALUES (?,?,?,'Student',?)", 
                                           (auto_student_id, sid, hashed_pass, full_name))
                            conn.commit()
                            st.success(f"✅ Student Added! Login ID: `{auto_student_id}` | Default Password: `{dob_str}`")
                        except sqlite3.IntegrityError:
                            st.error("Student ID/SR Number already exists!")

        elif choice == "Add Teacher / Staff":
            st.subheader("➕ Add Teacher or Staff Member")
            with st.form("add_teacher"):
                t_id = st.text_input("Teacher/Staff ID")
                t_name = st.text_input("Full Name")
                t_role = st.selectbox("Role Type", ["Teacher", "Accountant", "Staff"])
                t_pass = st.text_input("Assign Password", type="password")
                t_class = st.text_input("Class Teacher Of (If Applicable)")
                t_phone = st.text_input("Phone Number")

                if st.form_submit_button("Save Staff Account"):
                    is_valid, msg = is_strong_password(t_pass)
                    if not is_valid:
                        st.error(msg)
                    else:
                        try:
                            hashed = make_hashes(t_pass)
                            cursor.execute("INSERT INTO teachers VALUES (?,?,?,?,?,?,?)", (t_id, sid, t_name, t_role, t_class, "", t_phone))
                            cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)", (t_id, sid, hashed, t_role, t_name))
                            conn.commit()
                            st.success(f"{t_role} Account Created!")
                        except sqlite3.IntegrityError:
                            st.error("ID Already Exists!")

        elif choice == "Update School Data":
            st.subheader("📋 Update / View Student Directory")
            st.dataframe(pd.read_sql_query(f"SELECT * FROM students WHERE school_id = '{sid}'", conn), use_container_width=True)

        elif choice == "Mark Daily Attendance":
            st.subheader("📝 Attendance Marker (Staff & Students)")
            users_df = pd.read_sql_query(f"SELECT user_id, name, role FROM users WHERE school_id = '{sid}'", conn)
            if not users_df.empty:
                selected_person = st.selectbox("Select Person", users_df['user_id'] + " - " + users_df['name'] + " (" + users_df['role'] + ")")
                p_id = selected_person.split(" - ")[0]
                p_role = users_df[users_df['user_id'] == p_id]['role'].values[0]
                status = st.radio("Status", ["Present", "Absent"])
                date_str = str(datetime.now().date())
                
                if st.button("Mark Attendance"):
                    cursor.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?)", (p_id, sid, p_role, date_str, status))
                    conn.commit()
                    st.success(f"Attendance marked as {status} for {date_str}!")

    # 3. TEACHER DASHBOARD
    elif role == "Teacher":
        st.title("👩‍🏫 Teacher Dashboard")
        menu = ["Mark Student/Staff Attendance", "Upload Exam Marks"]
        choice = st.sidebar.radio("Navigation", menu)

        if choice == "Mark Student/Staff Attendance":
            st.subheader("📝 Daily Attendance Marker")
            s_df = pd.read_sql_query(f"SELECT user_id, name, role FROM users WHERE school_id = '{sid}'", conn)
            if not s_df.empty:
                person = st.selectbox("Select Person", s_df['user_id'] + " - " + s_df['name'] + " (" + s_df['role'] + ")")
                p_id = person.split(" - ")[0]
                p_role = s_df[s_df['user_id'] == p_id]['role'].values[0]
                status = st.radio("Status", ["Present", "Absent"])
                date_str = str(datetime.now().date())
                
                if st.button("Submit Attendance"):
                    cursor.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, ?)", (p_id, sid, p_role, date_str, status))
                    conn.commit()
                    st.success(f"Attendance marked as {status}!")

        elif choice == "Upload Exam Marks":
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
        
        tab1, tab2, tab3 = st.tabs(["👤 Profile & Details", "📊 Marks & Performance", "📅 Attendance History"])
        
        with tab1:
            st.subheader("Student Profile")
            profile = pd.read_sql_query(f"SELECT * FROM students WHERE student_id = '{u_id}'", conn)
            st.dataframe(profile, use_container_width=True)
            
        with tab2:
            st.subheader("Exam Marks")
            marks = pd.read_sql_query(f"SELECT exam_type, subject, marks_obtained, max_marks FROM marks WHERE student_id = '{u_id}'", conn)
            st.dataframe(marks, use_container_width=True)

        with tab3:
            st.subheader("Attendance History")
            att = pd.read_sql_query(f"SELECT date, status FROM attendance WH
