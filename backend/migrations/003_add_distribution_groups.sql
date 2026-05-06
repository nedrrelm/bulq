-- Migration: Add distribution groups for organizing pickup points
-- Each run gets a default distribution group; leader can create additional groups.

CREATE TABLE IF NOT EXISTS distribution_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_distribution_groups_run_id ON distribution_groups(run_id);

ALTER TABLE run_participations
    ADD COLUMN IF NOT EXISTS distribution_group_id UUID REFERENCES distribution_groups(id);
