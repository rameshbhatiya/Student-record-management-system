import sqlite3
import sys

# Database initialization
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            total_fee REAL NOT NULL,
            paid_fee REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_student():
    print("\n--- Add New Student ---")
    name = input("Enter Student Name: ").strip()
    course = input("Enter Course Name: ").strip()
    try:
        total_fee = float(input("Enter Total Course Fee: "))
        paid_fee = float(input("Enter Paid Amount: "))
    except ValueError:
        print("Invalid amount. Please enter numeric values.")
        return

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (name, course, total_fee, paid_fee) VALUES (?, ?, ?, ?)",
        (name, course, total_fee, paid_fee)
    )
    conn.commit()
    conn.close()
    print("Student record added successfully!")

def view_students():
    print("\n--- All Student Records ---")
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    records = cursor.fetchall()
    conn.close()

    if not records:
        print("No student records found.")
        return

    print("-" * 75)
    print(f"{'ID':<5} | {'Name':<20} | {'Course':<15} | {'Total Fee':<10} | {'Paid Fee':<10} | {'Pending':<10}")
    print("-" * 75)
    for row in records:
        sid, name, course, total_fee, paid_fee = row
        pending = total_fee - paid_fee
        print(f"{sid:<5} | {name:<20} | {course:<15} | ₹{total_fee:<9.2f} | ₹{paid_fee:<9.2f} | ₹{pending:<9.2f}")
    print("-" * 75)

def update_payment():
    print("\n--- Update Fee Payment ---")
    try:
        sid = int(input("Enter Student ID: "))
        amount = float(input("Enter Payment Amount: "))
    except ValueError:
        print("Invalid input.")
        return

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT paid_fee FROM students WHERE id = ?", (sid,))
    record = cursor.fetchone()

    if record:
        new_paid = record[0] + amount
        cursor.execute("UPDATE students SET paid_fee = ? WHERE id = ?", (new_paid, sid))
        conn.commit()
        print("Payment updated successfully!")
    else:
        print("Student ID not found.")
    
    conn.close()

def delete_student():
    print("\n--- Delete Student Record ---")
    try:
        sid = int(input("Enter Student ID to delete: "))
    except ValueError:
        print("Invalid ID.")
        return

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (sid,))
    if cursor.rowcount > 0:
        print("Student record deleted successfully!")
    else:
        print("Student ID not found.")
    conn.commit()
    conn.close()

def main():
    init_db()
    while True:
        print("\n=========================================")
        print(" STUDENT RECORD MANAGEMENT SYSTEM (CLI)")
        print("=========================================")
        print("1. Add Student Record")
        print("2. View All Students & Financials")
        print("3. Update Fee Payment")
        print("4. Delete Student Record")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            view_students()
        elif choice == "3":
            update_payment()
        elif choice == "4":
            delete_student()
        elif choice == "5":
            print("Exiting System. Good luck!")
            sys.exit()
        else:
            print("Invalid choice. Please choose between 1 and 5.")

if __name__ == "__main__":
    main()
