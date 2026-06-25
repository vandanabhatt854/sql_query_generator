from datetime import date, datetime

from sqlalchemy import insert

from .database import Base, engine, SessionLocal
from .models import Department, Employee, Student, QueryHistory


def seed_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        if session.query(Department).count():
            return
        departments = [
            Department(id=1, name="IT", location="Bengaluru"),
            Department(id=2, name="HR", location="Mumbai"),
            Department(id=3, name="Finance", location="Delhi"),
            Department(id=4, name="Sales", location="Hyderabad"),
        ]
        employees = [
            Employee(id=1, name="Aarav Sharma", department="IT", department_id=1, salary=65000, join_date=date(2022, 1, 12), email="aarav@example.com"),
            Employee(id=2, name="Priya Nair", department="HR", department_id=2, salary=54000, join_date=date(2021, 7, 3), email="priya@example.com"),
            Employee(id=3, name="Kabir Singh", department="IT", department_id=1, salary=92000, join_date=date(2020, 11, 20), email="kabir@example.com"),
            Employee(id=4, name="Ananya Iyer", department="Finance", department_id=3, salary=78000, join_date=date(2023, 2, 14), email="ananya@example.com"),
            Employee(id=5, name="Rohit Verma", department="Sales", department_id=4, salary=45000, join_date=date(2022, 5, 9), email="rohit@example.com"),
            Employee(id=6, name="Sneha Gupta", department="IT", department_id=1, salary=51000, join_date=date(2023, 8, 1), email="sneha@example.com"),
            Employee(id=7, name="Vikram Joshi", department="Sales", department_id=4, salary=61000, join_date=date(2019, 3, 18), email="vikram@example.com"),
            Employee(id=8, name="Meera Patel", department="HR", department_id=2, salary=57000, join_date=date(2020, 9, 30), email="meera@example.com"),
            Employee(id=9, name="Dev Kumar", department="Finance", department_id=3, salary=83000, join_date=date(2021, 12, 5), email="dev@example.com"),
            Employee(id=10, name="Nisha Rao", department="IT", department_id=1, salary=70000, join_date=date(2024, 1, 22), email="nisha@example.com"),
            Employee(id=11, name="Imran Khan", department="Sales", department_id=4, salary=49000, join_date=date(2023, 4, 17), email="imran@example.com"),
            Employee(id=12, name="Pooja Menon", department="HR", department_id=2, salary=62000, join_date=date(2022, 10, 10), email="pooja@example.com"),
            Employee(id=13, name="Aditya Bose", department="Finance", department_id=3, salary=88000, join_date=date(2020, 6, 25), email="aditya@example.com"),
            Employee(id=14, name="Sara Ali", department="IT", department_id=1, salary=76000, join_date=date(2021, 1, 8), email="sara@example.com"),
            Employee(id=15, name="Karan Mehta", department="Sales", department_id=4, salary=53000, join_date=date(2024, 3, 11), email="karan@example.com"),
        ]
        students = [
            Student(id=1, name="Arjun", course="Computer Science", cgpa=9.4, semester=6, email="arjun@college.edu"),
            Student(id=2, name="Diya", course="Data Science", cgpa=8.9, semester=4, email="diya@college.edu"),
            Student(id=3, name="Riya", course="Electronics", cgpa=9.1, semester=5, email="riya@college.edu"),
            Student(id=4, name="Mohan", course="Computer Science", cgpa=7.8, semester=6, email="mohan@college.edu"),
            Student(id=5, name="Aisha", course="Mathematics", cgpa=9.8, semester=2, email="aisha@college.edu"),
            Student(id=6, name="Rahul", course="Data Science", cgpa=8.2, semester=4, email="rahul@college.edu"),
            Student(id=7, name="Nandini", course="AI", cgpa=9.6, semester=8, email="nandini@college.edu"),
            Student(id=8, name="Sanjay", course="Mechanical", cgpa=7.2, semester=3, email="sanjay@college.edu"),
            Student(id=9, name="Kriti", course="AI", cgpa=9.0, semester=8, email="kriti@college.edu"),
            Student(id=10, name="Farhan", course="Business", cgpa=8.4, semester=5, email="farhan@college.edu"),
            Student(id=11, name="Neha", course="Economics", cgpa=8.7, semester=6, email="neha@college.edu"),
            Student(id=12, name="Ishaan", course="Computer Science", cgpa=9.2, semester=2, email="ishaan@college.edu"),
            Student(id=13, name="Tanvi", course="Law", cgpa=8.1, semester=4, email="tanvi@college.edu"),
            Student(id=14, name="Vivek", course="Physics", cgpa=7.9, semester=7, email="vivek@college.edu"),
            Student(id=15, name="Zoya", course="Chemistry", cgpa=9.3, semester=1, email="zoya@college.edu"),
        ]
        session.add_all(departments + employees + students)
        session.commit()
    finally:
        session.close()

