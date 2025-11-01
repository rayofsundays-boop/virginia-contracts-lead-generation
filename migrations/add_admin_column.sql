-- Migration: Add is_admin column to leads table
-- Purpose: Allow database-driven admin privileges instead of just hardcoded credentials
-- Date: 2025-11-01

-- Add is_admin column to leads table
ALTER TABLE leads ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

-- Create an index for faster admin lookups
CREATE INDEX IF NOT EXISTS idx_leads_is_admin ON leads(is_admin);

-- Optional: Make an existing user an admin (uncomment and replace with actual email)
-- UPDATE leads SET is_admin = TRUE WHERE email = 'your-admin@example.com';

-- Verify the change
-- SELECT id, email, username, is_admin FROM leads WHERE is_admin = TRUE;
