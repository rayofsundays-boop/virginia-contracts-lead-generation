-- Complete PostgreSQL Migration for Admin System
-- Run this in your Render PostgreSQL database shell
-- Date: 2025-11-01

-- Step 1: Add is_admin column to leads table
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'is_admin'
    ) THEN
        ALTER TABLE leads ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Column is_admin added successfully';
    ELSE
        RAISE NOTICE 'Column is_admin already exists';
    END IF;
END $$;

-- Step 2: Create an index for faster admin lookups
CREATE INDEX IF NOT EXISTS idx_leads_is_admin ON leads(is_admin);

-- Step 3: Verify the column was added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'leads' AND column_name = 'is_admin';

-- Step 4: Grant yourself admin privileges (UPDATE THIS EMAIL!)
-- Uncomment the line below and replace with your actual email address:
-- UPDATE leads SET is_admin = TRUE WHERE email = 'your-actual-email@example.com';

-- Step 5: Verify admin user was created
-- SELECT id, email, contact_name, is_admin FROM leads WHERE is_admin = TRUE;
