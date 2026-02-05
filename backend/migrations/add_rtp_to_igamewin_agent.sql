-- Migration: Add RTP field to igamewin_agents table
-- Date: 2026-02-05

-- Add rtp column to igamewin_agents table
ALTER TABLE igamewin_agents 
ADD COLUMN IF NOT EXISTS rtp FLOAT DEFAULT 96.0 NOT NULL;

-- Update existing records to have default RTP value
UPDATE igamewin_agents 
SET rtp = 96.0 
WHERE rtp IS NULL;
