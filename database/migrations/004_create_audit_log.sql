-- Migration 004: Create audit log table
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  event_details TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
