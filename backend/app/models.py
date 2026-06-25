from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class Department(Base):
    __tablename__ = "Department"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    location = Column(String(100), nullable=False)
    employees = relationship("Employee", back_populates="department_rel")


class Employee(Base):
    __tablename__ = "Employee"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("Department.id"), nullable=True, index=True)
    salary = Column(Float, nullable=False)
    join_date = Column(Date, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department_rel = relationship("Department", back_populates="employees")


class Student(Base):
    __tablename__ = "Students"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, index=True)
    course = Column(String(120), nullable=False)
    cgpa = Column(Float, nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    email = Column(String(150), unique=True, nullable=False)


class QueryHistory(Base):
    __tablename__ = "QueryHistory"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    nl_input = Column(Text, nullable=False)
    sql_generated = Column(Text, nullable=False)
    query_chosen = Column(Text, nullable=False)
    rows_affected = Column(Integer, nullable=True)
    rows_returned = Column(Integer, nullable=True)
    execution_status = Column(String(50), nullable=False)
    risk_warning = Column(Text, nullable=True)

