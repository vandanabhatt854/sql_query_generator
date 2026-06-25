-- Student schema definition
CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  enrollment_date DATE,
  major TEXT,
  gpa REAL
);
