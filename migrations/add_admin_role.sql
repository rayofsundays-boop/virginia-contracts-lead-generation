-- Add admin_role column to leads table for role-based access control
-- Run this migration on Render PostgreSQL database

DO $$ 
BEGIN
    -- Add admin_role column if it doesn't exist
    -- Values: 'super_admin', 'admin', NULL (for regular users)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'admin_role'
    ) THEN
        ALTER TABLE leads ADD COLUMN admin_role TEXT DEFAULT NULL;
        
        -- Set existing is_admin=TRUE users to 'super_admin'
        UPDATE leads SET admin_role = 'super_admin' WHERE is_admin = TRUE;
        
        RAISE NOTICE 'Added admin_role column to leads table';
    ELSE
        RAISE NOTICE 'admin_role column already exists';
    END IF;
END $$;
