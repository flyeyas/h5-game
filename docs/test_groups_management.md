# Test User Groups Management Command

## Overview

This document provides instructions for using the Django management command `create_test_groups` to batch create 20 test user groups with appropriate permissions for testing purposes in the Django admin backend.

## Command Location

The management command is located at:
```
games/management/commands/create_test_groups.py
```

## Features

1. **Batch Creation**: Creates 20 meaningful test user groups with English names
2. **Permission Assignment**: Automatically assigns appropriate permissions to each group
3. **Duplicate Prevention**: Safely checks for existing groups and skips creation if they already exist
4. **Safe Execution**: Can be run multiple times without creating duplicates
5. **Preview Mode**: Dry-run option to preview what will be created
6. **Clear Function**: Option to clear existing test groups before creating new ones
7. **Verification**: Automatic data verification after creation

## Created User Groups

The command creates the following 20 test user groups:

1. **Super Admin Test Group** - All permissions (44 permissions)
2. **Game Admin Test Group** - Game and category management (8 permissions)
3. **Category Admin Test Group** - Category management only (4 permissions)
4. **Advertisement Admin Test Group** - Advertisement management (4 permissions)
5. **Content Editor Test Group** - Content editing permissions (8 permissions)
6. **Game Developer Test Group** - Game development permissions (4 permissions)
7. **Data Analyst Test Group** - View permissions for analysis (11 permissions)
8. **Customer Service Test Group** - Customer service permissions (11 permissions)
9. **QA Tester Test Group** - Testing permissions (11 permissions)
10. **Operations Test Group** - Operations management (8 permissions)
11. **Content Moderator Test Group** - Content moderation (8 permissions)
12. **Finance Team Test Group** - Financial management (4 permissions)
13. **Technical Support Test Group** - Technical support (11 permissions)
14. **Marketing Team Test Group** - Marketing permissions (15 permissions)
15. **Product Manager Test Group** - Product management (19 permissions)
16. **UI/UX Designer Test Group** - Design permissions (11 permissions)
17. **Intern Test Group** - Limited permissions for interns (5 permissions)
18. **External Partner Test Group** - Partner access (11 permissions)
19. **Guest Access Test Group** - Minimal guest permissions (3 permissions)
20. **System Monitor Test Group** - System monitoring (11 permissions)

## Usage Instructions

### Basic Usage

To create all 20 test user groups:

```bash
python manage.py create_test_groups
```

### Preview Mode (Recommended First)

To see what will be created without actually creating the groups:

```bash
python manage.py create_test_groups --dry-run
```

### Clear Existing Test Groups

To clear all existing test groups (groups containing "Test" in their names):

```bash
python manage.py create_test_groups --clear
```

### Clear and Recreate

To clear existing test groups and create new ones:

```bash
python manage.py create_test_groups --clear
```

### Preview Clear Operation

To see what would be cleared without actually deleting:

```bash
python manage.py create_test_groups --clear --dry-run
```

## Command Options

- `--dry-run`: Preview mode - shows what would be created/deleted without making changes
- `--clear`: Clears all existing test groups before creating new ones
- `-v 2`: Verbose output for debugging

## Expected Output

### Successful Creation
```
============================================================
Starting bulk creation of test user groups
============================================================

----------------------------------------
Creating test user groups...
----------------------------------------
Successfully created user group: Super Admin Test Group (Permissions count: 44)
Successfully created user group: Game Admin Test Group (Permissions count: 8)
...

----------------------------------------
Creation Result Summary:
----------------------------------------
Successfully created user groups: 20
Skipped user groups: 0

----------------------------------------
Data Verification:
----------------------------------------
Total test user groups in database: 20
User groups with permissions: 20
Total permission assignments: 208
Average permissions per group: 10.4

Verification completed! You can view the results at:
http://127.0.0.1:8000/en/admin/auth/group/
http://127.0.0.1:8000/admin/auth/group/
============================================================
```

### Safe Duplicate Handling
When run again, the command will safely skip existing groups:
```
User group "Super Admin Test Group" already exists, skipping creation
User group "Game Admin Test Group" already exists, skipping creation
...
Successfully created user groups: 0
Skipped user groups: 20
```

## Verification

After running the command, you can verify the results by:

1. **Command Line Verification**: The command automatically verifies data and shows statistics
2. **Django Admin Interface**: Visit the URLs provided in the output:
   - http://127.0.0.1:8000/en/admin/auth/group/
   - http://127.0.0.1:8000/admin/auth/group/

## Permission Structure

The groups are assigned permissions based on their roles:

- **Admin Groups**: Full CRUD permissions for their respective areas
- **Editor Groups**: Create, read, update permissions
- **Analyst Groups**: Primarily view permissions
- **Support Groups**: View and limited modification permissions
- **Intern/Guest Groups**: Minimal view permissions

## Safety Features

1. **Duplicate Prevention**: Checks for existing groups before creation
2. **Transaction Safety**: Uses database transactions for atomic operations
3. **Error Handling**: Graceful error handling with detailed error messages
4. **Rollback Support**: Failed operations don't leave partial data

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have Django admin permissions
2. **Database Connection**: Verify Django database settings
3. **Missing Models**: Ensure all required models are migrated

### Debug Mode

For detailed debugging information:
```bash
python manage.py create_test_groups --dry-run -v 2
```

## Integration with Django Admin

The created groups will appear in the Django admin interface at:
- **English Admin**: http://127.0.0.1:8000/en/admin/auth/group/
- **Default Admin**: http://127.0.0.1:8000/admin/auth/group/

Each group can be:
- Viewed and edited through the admin interface
- Assigned to users
- Modified with additional permissions
- Used for role-based access control

## Notes

- Default language is English as specified in requirements
- All group names contain "Test" for easy identification and cleanup
- Permission assignments are based on Django's built-in permission system
- The command is safe to run in production environments due to its safety checks
