-- Add cancellation tracking columns to leads table

-- For SQLite (local development)
ALTER TABLE leads ADD COLUMN cancellation_reason TEXT;
ALTER TABLE leads ADD COLUMN cancellation_date TIMESTAMP;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_leads_cancellation ON leads(cancellation_date);
