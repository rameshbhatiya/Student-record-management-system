import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="School Student Management System",
    page_icon="🏫",
    layout="wide"
)

# Database Setup
def init_db():
    conn = sqlite3.connect("school_students.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_no INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            student_class TEXT NOT NULL,
            section TEXT NOT NULL,
            gender TEXT,
            dob DATE,
            father_name TEXT,
            phone TEXT,
            address TEXT,
            total_fee REAL DEFAULT 0,
            paid_fee REAL DEFAULT 0
        )
    """)
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size:28px;
        font-weight:bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏫 School Student Record Management System</div>', unsafe_allow_html=True)

# Sidebar Menu Options
menu = [
    "📊 Dashboard",
    "➕ Student Registration",
    "📋 All Records & Class Filter",
    "💳 Fee Management & Receipt",
    "🔍 Search Student Profile",
    "⚙️ Update / Delete Record"
]

choice = st.sidebar.selectbox("📌 Main Menu", menu)

# -------------------------------------------------------------
# 1. DASHBOARD OVERVIEW
# -------------------------------------------------------------
if choice == "📊 Dashboard":
    st.subheader("📊 School Quick Overview")
    
    df = pd.read_sql_query("SELECT *, (total_fee - paid_fee) as pending_fee FROM students", conn)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Students Registered", len(df))
    with col2:
        total_collected = df['paid_fee'].sum() if not df.empty else 0
        st.metric("Total Fees Collected", f"₹{total_collected:,.2f}")
    with col3:
        total_pending = df['pending_fee'].sum() if not df.empty else 0
        st.metric("Total Pending Fees", f"₹{total_pending:,.2f}")
    with col4:
        active_classes = df['student_class'].nunique() if not df.empty else 0
        st.metric("Active Classes", active_classes)

    st.markdown("---")
    st.write("### 📈 Recent Registered Students")
    if not df.empty:
        st.dataframe(df.tail(5)[['roll_no', 'name', 'student_class', 'section', 'phone']], use_container_width=True)
    else:
        st.info("No records available yet. Go to 'Student Registration' to add students.")

# -------------------------------------------------------------
# 2. STUDENT REGISTRATION
# -------------------------------------------------------------
elif choice == "➕ Student Registration":
    st.subheader("➕ New Student Admission / Registration")
    
    with st.form("admission_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            roll_no = st.number_input("Roll Number*", min_value=1, step=1)
            name = st.text_input("Full Name*")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
        with col2:
            student_class = st.selectbox("Class*", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", 
                                                    "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", 
                                                    "Class 11", "Class 12"])
            section = st.selectbox("Section*", ["A", "B", "C", "D"])
            dob = st.date_input("Date of Birth")

        with col3:
            father_name = st.text_input("Father / Guardian Name*")
            phone = st.text_input("Contact Mobile No.*")
            address = st.text_area("Home Address", height=100)

        st.markdown("#### 💰 Annual Fee Structure Setup")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            total_fee = st.number_input("Total Annual Fee Structure (₹)*", min_value=0.0, value=25000.0, step=500.0)
        with col_f2:
            paid_fee = st.number_input("Initial Advance Paid Fee (₹)", min_value=0.0, value=0.0, step=500.0)

        submit = st.form_submit_button("Submit & Save Record")

        if submit:
            if not name or not phone or not father_name:
                st.error("Please fill all compulsory fields marked with *")
            else:
                try:
                    cursor.execute("""
                        INSERT INTO students 
                        (roll_no, name, student_class, section, gender, dob, father_name, phone, address, total_fee, paid_fee)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (roll_no, name, student_class, section, gender, str(dob), father_name, phone, address, total_fee, paid_fee))
                    conn.commit()
                    st.success(f"✅ Student {name} (Roll No: {roll_no}) successfully registered!")
                except sqlite3.IntegrityError:
                    st.error(f"❌ Roll Number {roll_no} already exists! Please use a unique Roll Number.")

# -------------------------------------------------------------
# 3. ALL RECORDS & CLASS FILTER
# -------------------------------------------------------------
elif choice == "📋 All Records & Class Filter":
    st.subheader("📋 Student Records Directory")
    
    df = pd.read_sql_query("SELECT *, (total_fee - paid_fee) as pending_fee FROM students", conn)
    
    if df.empty:
        st.warning("No records found in database!")
    else:
        col1, col2 = st.columns(2)
        with col1:
            class_filter = st.multiselect("Filter by Class", options=df['student_class'].unique(), default=df['student_class'].unique())
        with col2:
            section_filter = st.multiselect("Filter by Section", options=df['section'].unique(), default=df['section'].unique())

        filtered_df = df[(df['student_class'].isin(class_filter)) & (df['section'].isin(section_filter))]
        
        st.write(f"Showing **{len(filtered_df)}** records")
        st.dataframe(filtered_df, use_container_width=True)

        # Download CSV Option
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Filtered Data to CSV", data=csv, file_name="student_records.csv", mime="text/csv")

# -------------------------------------------------------------
# 4. FEE MANAGEMENT & RECEIPT
# -------------------------------------------------------------
elif choice == "💳 Fee Management & Receipt":
    st.subheader("💳 Fee Collection & Receipt Generator")
    
    roll_input = st.number_input("Enter Student Roll Number", min_value=1, step=1)
    
    if st.button("Fetch Fee Details"):
        cursor.execute("SELECT roll_no, name, student_class, section, total_fee, paid_fee FROM students WHERE roll_no = ?", (roll_input,))
        student = cursor.fetchone()
        if student:
            st.session_state['fee_student'] = student
        else:
            st.error("Student Roll Number not found!")
            if 'fee_student' in st.session_state:
                del st.session_state['fee_student']

    if 'fee_student' in st.session_state:
        s = st.session_state['fee_student']
        roll, name, cls, sec, total_f, paid_f = s
        pending = total_f - paid_f
        
        st.info(f"**Student:** {name} | **Class:** {cls}-{sec} | **Total Fee:** ₹{total_f:,.2f} | **Paid:** ₹{paid_f:,.2f} | **Pending:** ₹{pending:,.2f}")
        
        with st.form("fee_deposit_form"):
            deposit = st.number_input("Enter Amount to Deposit (₹)", min_value=1.0, max_value=float(pending) if pending > 0 else 1.0, step=100.0)
            payment_mode = st.selectbox("Payment Mode", ["Cash", "Online / UPI", "Cheque", "Bank Transfer"])
            pay_btn = st.form_submit_button("Record Payment & Generate Receipt")
            
            if pay_btn:
                new_paid = paid_f + deposit
                cursor.execute("UPDATE students SET paid_fee = ? WHERE roll_no = ?", (new_paid, roll))
                conn.commit()
                st.success("✅ Payment recorded successfully!")
                
                # Printable Receipt Summary
                st.markdown("---")
                st.markdown("### 🧾 Payment Receipt")
                st.markdown(f"""
                **Receipt Date:** {datetime.now().strftime('%d-%b-%Y %I:%M %p')}  
                **Roll No:** {roll} | **Student Name:** {name}  
                **Class:** {cls} ({sec})  
                ---
                - **Amount Paid Now:** ₹{deposit:,.2f} ({payment_mode})  
                - **Total Fee Paid Till Date:** ₹{new_paid:,.2f}  
                - **Remaining Balance Fee:** ₹{(total_f - new_paid):,.2f}  
                """)
                del st.session_state['fee_student']

# -------------------------------------------------------------
# 5. SEARCH STUDENT PROFILE
# -------------------------------------------------------------
elif choice == "🔍 Search Student Profile":
    st.subheader("🔍 Search Student Profile")
    
    search_query = st.text_input("Enter Student Roll No, Name, or Mobile Number")
    
    if search_query:
        query = f"%{search_query}%"
        cursor.execute("""
            SELECT * FROM students 
            WHERE roll_no LIKE ? OR name LIKE ? OR phone LIKE ?
        """, (query, query, query))
        results = cursor.fetchall()
        
        if results:
            for row in results:
                st.markdown(f"### 👤 {row[1]} (Roll No: {row[0]})")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Class:** {row[2]} ({row[3]})")
                    st.write(f"**Gender:** {row[4]}")
                    st.write(f"**DOB:** {row[5]}")
                with col2:
                    st.write(f"**Father's Name:** {row[6]}")
                    st.write(f"**Phone:** {row[7]}")
                    st.write(f"**Address:** {row[8]}")
                with col3:
                    st.write(f"**Total Fee:** ₹{row[9]:,.2f}")
                    st.write(f"**Paid Fee:** ₹{row[10]:,.2f}")
                    st.write(f"**Pending Fee:** ₹{(row[9] - row[10]):,.2f}")
                st.markdown("---")
        else:
            st.warning("No student profile found with given input.")

# -------------------------------------------------------------
# 6. UPDATE / DELETE RECORD
# -------------------------------------------------------------
elif choice == "⚙️ Update / Delete Record":
    st.subheader("⚙️ Manage Student Records")
    
    action = st.radio("Select Action", ["Update Student Details", "Delete Student"])
    roll_input = st.number_input("Enter Student Roll Number to Modify", min_value=1, step=1)
    
    if action == "Update Student Details":
        cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_input,))
        student = cursor.fetchone()
        
        if student:
            st.write(f"Modifying record for: **{student[1]}**")
            with st.form("update_form"):
                u_name = st.text_input("Name", value=student[1])
                u_class = st.selectbox("Class", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", 
                                                 "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", 
                                                 "Class 11", "Class 12"], index=0)
                u_section = st.selectbox("Section", ["A", "B", "C", "D"], index=0)
                u_father = st.text_input("Father Name", value=student[6])
                u_phone = st.text_input("Phone", value=student[7])
                u_total = st.number_input("Total Fee (₹)", value=float(student[9]))
                
                if st.form_submit_button("Update Details"):
                    cursor.execute("""
                        UPDATE students 
                        SET name=?, student_class=?, section=?, father_name=?, phone=?, total_fee=?
                        WHERE roll_no=?
                    """, (u_name, u_class, u_section, u_father, u_phone, u_total, roll_input))
                    conn.commit()
                    st.success("✅ Student details updated successfully!")
        else:
            st.info("Enter a valid Roll Number to load details.")

    elif action == "Delete Student":
        cursor.execute("SELECT name FROM students WHERE roll_no = ?", (roll_input,))
        student = cursor.fetchone()
        if student:
            st.error(f"Are you sure you want to delete **{student[0]}** (Roll No: {roll_input})?")
            if st.button("Confirm Delete Record"):
                cursor.execute("DELETE FROM students WHERE roll_no = ?", (roll_input,))
                conn.commit()
                st.success("Record deleted successfully!")
        else:
            st.info("Enter a valid Roll Number.")
