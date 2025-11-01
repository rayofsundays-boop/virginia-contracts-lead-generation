-- Add cancellation tracking columns to leads table (PostgreSQL version for Render)

DO $$ 
BEGIN
    -- Add cancellation_reason column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'cancellation_reason'
    ) THEN
        ALTER TABLE leads ADD COLUMN cancellation_reason TEXT;
    END IF;

    -- Add cancellation_date column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'leads' AND column_name = 'cancellation_date'
    ) THEN
        ALTER TABLE leads ADD COLUMN cancellation_date TIMESTAMP;
    END IF;
END $$;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_leads_cancellation ON leads(cancellation_date);

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'leads' 
AND column_name IN ('cancellation_reason', 'cancellation_date');
