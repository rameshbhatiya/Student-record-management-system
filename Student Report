#student-record-management-system
import pickle
import os

# Load student data safely
file_name = "Student_Report.pkl"
if os.path.exists(file_name):
    try:
        with open(file_name, "rb") as f:
            Student_Report = pickle.load(f)
    except:
        Student_Report = []
else:
    Student_Report = []

# Show Menu
print("--- Student Record System ---")
print("1. Student Name")
print("2. Student Class")
print("3. Roll Number")
print("4. Address")
print("5. Phone Number")
print("6. Father's Name")
print("7. Mother's Name")
print("8. Parents Phone Number")
print("9. Student Fees")
print("10. Fees Deposited")
print("11. Fees Remaining")
print("12. ADD Student Data")
print("13. Delete Student Data")

try:
    DATA = int(input("Enter your choice (1-13): "))
except ValueError:
    DATA = 999

# Handle Choices 1 to 11 (Viewing Student Data)
if 1 <= DATA <= 11:
    r_no = int(input("Enter the Roll Number of the student: "))
    found = False
    student = None
    
    for s in Student_Report:
        if s.get("RollNumber_of_Student") == r_no:
            found = True
            student = s
            break
            
    if found and student:
        if DATA == 1:
            print("Name:", student.get("Student_Name"))
        elif DATA == 2:
            print("Class:", student.get("Student_class"))
        elif DATA == 3:
            print("Roll Number:", student.get("RollNumber_of_Student"))
        elif DATA == 4:
            print("Address:", student.get("Address_of_Student"))
        elif DATA == 5:
            print("Phone Number:", student.get("PhoneNumber"))
        elif DATA == 6:
            print("Father's Name:", student.get("FNofStudent"))
        elif DATA == 7:
            print("Mother's Name:", student.get("MNofStudent"))
        elif DATA == 8:
            print("Parents Phone:", student.get("ParentsPhoneNumber"))
        elif DATA == 9:
            print("Total Fees:", student.get("StudentFees"))
        elif DATA == 10:
            print("Fees Deposited:", student.get("StudentFeesDeposited"))
        elif DATA == 11:
            print("Fees Remaining:", student.get("StudentFeesRemaining"))
    else:
        print("Student not found!")

# Handle Choice 12: Add Student Data
elif DATA == 12:
    new_student = {
        "Student_Name": input("Enter Student Name: "),
        "Student_class": input("Enter Student Class: "),
        "RollNumber_of_Student": int(input("Enter Roll Number: ")),
        "Address_of_Student": input("Enter Address: "),
        "PhoneNumber": input("Enter Phone Number: "),
        "FNofStudent": input("Enter Father's Name: "),
        "MNofStudent": input("Enter Mother's Name: "),
        "ParentsPhoneNumber": input("Enter Parents Phone Number: "),
        "StudentFees": float(input("Enter Total Fees: ")),
        "StudentFeesDeposited": float(input("Enter Fees Deposited: "))
    }
    new_student["StudentFeesRemaining"] = new_student["StudentFees"] - new_student["StudentFeesDeposited"]
    
    Student_Report.append(new_student)
    with open(file_name, "wb") as f:
        pickle.dump(Student_Report, f)
    print("Student data added successfully!")

# Handle Choice 13: Delete Student Data
elif DATA == 13:
    r_no = int(input("Enter Roll Number of student to delete: "))
    initial_length = len(Student_Report)
    Student_Report = [s for s in Student_Report if s.get("RollNumber_of_Student") != r_no]
    
    if len(Student_Report) < initial_length:
        with open(file_name, "wb") as f:
            pickle.dump(Student_Report, f)
        print("Student deleted successfully!")
    else:
        print("Student not found!")

else:
    print("404 NOT FOUND / Invalid Choice")

