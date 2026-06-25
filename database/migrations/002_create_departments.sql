-- Migration 002: Create departments table
CREATE TABLE departments (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  location TEXT
);
