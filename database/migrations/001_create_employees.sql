-- Migration 001: Create employees table
CREATE TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  department_id INTEGER,
  title TEXT,
  salary REAL,
  hired_date DATE
);
