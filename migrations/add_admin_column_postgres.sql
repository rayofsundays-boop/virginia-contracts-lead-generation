-- Migration: Add is_admin column to leads table (PostgreSQL version)
-- Purpose: Allow database-driven admin privileges instead of just hardcoded credentials
-- Date: 2025-11-01

-- Add is_admin column to leads table (if it doesn't exist)
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'is_admin'
    ) THEN
        ALTER TABLE leads ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Create an index for faster admin lookups
CREATE INDEX IF NOT EXISTS idx_leads_is_admin ON leads(is_admin);

-- Verify the change
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'leads' AND column_name = 'is_admin';
