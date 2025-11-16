-- Fix saved_leads table schema for SQLite
-- Run this on SQLite databases that have the old schema

ALTER TABLE saved_leads ADD COLUMN IF NOT EXISTS lead_title TEXT;
ALTER TABLE saved_leads ADD COLUMN IF NOT EXISTS lead_data TEXT;
ALTER TABLE saved_leads ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'saved';
ALTER TABLE saved_leads ADD COLUMN IF NOT EXISTS saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE saved_leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Note: lead_id should ideally be TEXT but SQLite doesn't support changing column types
-- The application code now converts lead_id to string to handle this
