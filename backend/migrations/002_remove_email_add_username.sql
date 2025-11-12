-- Migration: Remove email field, make username required
-- This migration copies email to username where username is null, then removes email column
--
-- HOW TO RUN IN PRODUCTION:
--
-- 1. Stop the backend application to prevent new writes during migration
--
-- 2. Backup your database first:
--    pg_dump -U bulq_user -d bulq_db > backup_before_username_migration.sql
--
-- 3. Run this migration:
--    psql -U bulq_user -d bulq_db -f backend/migrations/002_remove_email_add_username.sql
--
-- 4. Verify the migration succeeded:
--    psql -U bulq_user -d bulq_db -c "\d users"
--    (Should show 'username' column as NOT NULL, 'email' column should be gone)
--
-- 5. Deploy the new backend code that uses username instead of email
--
-- 6. Restart the backend application
--
-- NOTE: This is a breaking change. The old backend code will not work after this migration.
--       Make sure to deploy the updated backend immediately after running the migration.

-- Step 1: Copy email to username where username is null
UPDATE users
SET username = email
WHERE username IS NULL;

-- Step 2: Make username NOT NULL
ALTER TABLE users
ALTER COLUMN username SET NOT NULL;

-- Step 3: Drop the email column
ALTER TABLE users
DROP COLUMN email;
