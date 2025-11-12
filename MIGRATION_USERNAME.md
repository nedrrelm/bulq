# Username-Only Authentication Migration

**Date:** 2025-11-12
**Status:** ✅ COMPLETED
**Migration Script:** `backend/migrations/002_remove_email_add_username.sql`

## Summary

The application has been migrated from email-based authentication to username-only authentication. Users now log in with a username instead of an email address.

## Changes Made

### Backend
- ✅ Removed `email` field from User model
- ✅ Made `username` field required and unique
- ✅ Updated all repository methods (`get_user_by_username` instead of `get_user_by_email`)
- ✅ Updated authentication routes and schemas
- ✅ Updated admin service to search by username
- ✅ Updated seed data to use simple usernames (alice, bob, carol, test)

### Frontend
- ✅ Updated login form to use username input
- ✅ Updated registration form with username validation
- ✅ Updated user type definitions
- ✅ Updated group member display to show @username
- ✅ Updated all API calls to use username

### Username Validation
- Minimum 3 characters, maximum 50 characters
- Allowed characters: letters (a-z, A-Z), numbers (0-9), hyphens (-), underscores (_)
- Case-insensitive (automatically converted to lowercase)
- Must be unique across all users

## Production Deployment Steps

### 1. Preparation
```bash
# Backup the database
pg_dump -U bulq_user -d bulq_db > backup_before_username_migration_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Stop the Application
```bash
docker-compose down
```

### 3. Run the Migration
```bash
psql -U bulq_user -d bulq_db -f backend/migrations/002_remove_email_add_username.sql
```

### 4. Verify Migration
```bash
# Check that the users table has been updated correctly
psql -U bulq_user -d bulq_db -c "\d users"

# Should show:
# - username column as "character varying NOT NULL"
# - email column should be GONE
# - ix_users_username index should exist
```

### 5. Deploy New Code
```bash
# Pull latest code
git pull origin master

# Rebuild and start containers
docker-compose build
docker-compose up -d
```

### 6. Verify Application
- Test user registration with a username
- Test login with existing username
- Verify that the login page shows "Username" instead of "Email"

## Rollback Procedure

If something goes wrong, you can rollback:

```bash
# Stop the application
docker-compose down

# Restore from backup
psql -U bulq_user -d bulq_db < backup_before_username_migration_TIMESTAMP.sql

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## Testing

After deployment, test the following:

1. ✅ New user registration with username
2. ✅ Login with existing username (migrated from email)
3. ✅ Group member display shows @username
4. ✅ Admin panel shows username instead of email
5. ✅ WebSocket notifications work correctly
6. ✅ All authentication flows (login, logout, session management)

## Notes

- **Breaking Change:** This is a breaking change. The old code will not work after the migration.
- **Existing Users:** For existing users, their email addresses were copied to the username field during migration
- **Case Sensitivity:** All usernames are stored in lowercase for consistency
- **No Email Storage:** Email addresses are no longer stored in the database

## Support

If you encounter issues:
1. Check application logs: `docker-compose logs backend`
2. Check database state: `psql -U bulq_user -d bulq_db -c "SELECT id, name, username FROM users LIMIT 5;"`
3. Restore from backup if needed (see Rollback Procedure above)
