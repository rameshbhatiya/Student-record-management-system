
"""
student_report.py
Student Report Module — Multi-School ERP

This module calculates academic performance and creates
a student report. It currently uses sample data; database
integration can be added through the main backend later.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SubjectResult:
    subject: str
    marks_obtained: float
    maximum_marks: float = 100.0

    @property
    def percentage(self) -> float:
        if self.maximum_marks <= 0:
            return 0.0

        return (self.marks_obtained / self.maximum_marks) * 100


@dataclass
class Student:
    student_id: str
    name: str
    school_id: str
    class_name: str
    section: str
    roll_number: str
    academic_year: str
    attendance_present: int = 0
    attendance_total: int = 0
    subjects: List[SubjectResult] = field(default_factory=list)


def calculate_grade(percentage: float) -> str:
    """Return a grade based on the percentage."""

    if percentage >= 90:
        return "A+"
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    if percentage >= 33:
        return "E"

    return "F"


def calculate_attendance(present: int, total: int) -> float:
    """Calculate attendance percentage safely."""

    if total <= 0 or present < 0 or present > total:
        return 0.0

    return round((present / total) * 100, 2)


def generate_student_report(student: Student) -> Dict:
    """
    Generate a structured report for one student.

    The school_id is included to support future multi-school
    database integration. The backend must verify that the
    logged-in user is authorized to access this school.
    """

    subject_reports = []

    total_marks = 0.0
    maximum_marks = 0.0

    for result in student.subjects:
        if result.maximum_marks <= 0:
            raise ValueError(
                f"Maximum marks must be positive for {result.subject}."
            )

        if not 0 <= result.marks_obtained <= result.maximum_marks:
            raise ValueError(
                f"Marks for {result.subject} must be between "
                f"0 and {result.maximum_marks}."
            )

        percentage = round(result.percentage, 2)

        subject_reports.append({
            "subject": result.subject,
            "marks_obtained": result.marks_obtained,
            "maximum_marks": result.maximum_marks,
            "percentage": percentage,
            "grade": calculate_grade(percentage),
        })

        total_marks += result.marks_obtained
        maximum_marks += result.maximum_marks

    overall_percentage = (
        round((total_marks / maximum_marks) * 100, 2)
        if maximum_marks > 0
        else 0.0
    )

    attendance_percentage = calculate_attendance(
        student.attendance_present,
        student.attendance_total,
    )

    return {
        "student": {
            "student_id": student.student_id,
            "name": student.name,
            "school_id": student.school_id,
            "class": student.class_name,
            "section": student.section,
            "roll_number": student.roll_number,
            "academic_year": student.academic_year,
        },
        "academic_performance": {
            "subjects": subject_reports,
            "total_marks_obtained": round(total_marks, 2),
            "total_maximum_marks": round(maximum_marks, 2),
            "overall_percentage": overall_percentage,
            "overall_grade": calculate_grade(overall_percentage),
        },
        "attendance": {
            "days_present": student.attendance_present,
            "total_school_days": student.attendance_total,
            "percentage": attendance_percentage,
        },
    }


def print_student_report(report: Dict) -> None:
    """Display a readable report in the terminal."""

    student = report["student"]
    academic = report["academic_performance"]
    attendance = report["attendance"]

    print("\n" + "=" * 48)
    print("              STUDENT REPORT")
    print("=" * 48)

    print(f"Student Name : {student['name']}")
    print(f"Student ID   : {student['student_id']}")
    print(f"School ID    : {student['school_id']}")
    print(f"Class        : {student['class']}")
    print(f"Section      : {student['section']}")
    print(f"Roll Number  : {student['roll_number']}")
    print(f"Academic Year: {student['academic_year']}")

    print("\n" + "-" * 48)
    print("ACADEMIC PERFORMANCE")
    print("-" * 48)

    print(
        f"{'Subject':<18}"
        f"{'Marks':<14}"
        f"{'Percent':<10}"
        f"Grade"
    )

    for subject in academic["subjects"]:
        marks = (
            f"{subject['marks_obtained']}/"
            f"{subject['maximum_marks']}"
        )

        print(
            f"{subject['subject']:<18}"
            f"{marks:<14}"
            f"{subject['percentage']:<10.2f}"
            f"{subject['grade']}"
        )

    print("-" * 48)
    print(
        f"Total Marks : {academic['total_marks_obtained']} / "
        f"{academic['total_maximum_marks']}"
    )
    print(f"Percentage  : {academic['overall_percentage']}%")
    print(f"Overall Grade: {academic['overall_grade']}")

    print("\nATTENDANCE")
    print("-" * 48)
    print(
        f"Present: {attendance['days_present']} / "
        f"{attendance['total_school_days']} days"
    )
    print(f"Attendance: {attendance['percentage']}%")
    print("=" * 48)


if __name__ == "__main__":
    # Demonstration data only — replace with real records later.
    demo_student = Student(
        student_id="STU-1001",
        name="Aarav Sharma",
        school_id="SCH-001",
        class_name="10",
        section="A",
        roll_number="12",
        academic_year="2026-2027",
        attendance_present=180,
        attendance_total=200,
        subjects=[
            SubjectResult("English", 86),
            SubjectResult("Mathematics", 92),
            SubjectResult("Science", 88),
            SubjectResult("Social Science", 81),
            SubjectResult("Computer", 95),
        ],
    )

    report = generate_student_report(demo_student)
    print_student_report(report)
        
