-- Add onboarding_disabled column to user_onboarding table
-- This allows users to permanently dismiss the onboarding modal

ALTER TABLE user_onboarding 
ADD COLUMN IF NOT EXISTS onboarding_disabled BOOLEAN DEFAULT FALSE;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_user_onboarding_disabled ON user_onboarding(onboarding_disabled);
