# Database Migrations

This directory contains SQL migration scripts for the Bulq database.

## Migration History

### 002_remove_email_add_username.sql
**Date:** 2025-11-12
**Status:** Breaking Change
**Description:** Removes email field from users table, replaces with username-only authentication

**Changes:**
- Copies email values to username field for existing users
- Makes username field NOT NULL
- Drops email column from users table

**Prerequisites:**
- Backup database before running
- Stop backend application during migration
- Deploy updated backend code immediately after migration

**How to run:**
```bash
# 1. Backup database
pg_dump -U bulq_user -d bulq_db > backup_before_username_migration.sql

# 2. Run migration
psql -U bulq_user -d bulq_db -f backend/migrations/002_remove_email_add_username.sql

# 3. Verify
psql -U bulq_user -d bulq_db -c "\d users"
```

## General Migration Guidelines

1. **Always backup** before running migrations
2. **Test migrations** in a development environment first
3. **Stop the application** during schema-changing migrations to prevent conflicts
4. **Verify success** after running migrations
5. **Deploy code changes** immediately after breaking migrations
6. **Document rollback** procedures for critical migrations

## Rollback Procedures

If you need to rollback a migration, you can restore from backup:
```bash
# Stop the application
docker-compose down

# Restore from backup
psql -U bulq_user -d bulq_db < backup_file.sql

# Redeploy old version of the code
git checkout <previous-commit>
docker-compose up -d
```
