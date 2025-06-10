# LDAP Admin Tool

A command-line administration tool for managing users and groups in the JSON-based LDAP server. This tool provides easy-to-use commands for adding, removing, and modifying LDAP entries without needing to manually edit JSON files.

## Features

- **User Management**: Add, remove, and modify user accounts
- **Group Management**: Create groups and manage member lists
- **Attribute Support**: Add custom attributes to users
- **JSON Validation**: Ensures data integrity when modifying files
- **Safe Operations**: Creates backups and validates JSON structure

## Requirements

- Python 3.7+
- Access to the `ldap-data/` directory

## Usage

The tool uses a command-line interface with subcommands for different operations.

### User Operations

#### Add a User
```bash
python ldap_admin.py user add <username> <password> [--attrs <json_attributes>]
```

**Examples:**
```bash
# Basic user
python ldap_admin.py user add john.doe secretpass

# User with additional attributes
python ldap_admin.py user add jane.doe mypassword --attrs '{"email": "jane@company.com", "cn": "Jane Doe", "department": "Engineering"}'
```

#### Remove a User
```bash
python ldap_admin.py user remove <username>
```

**Example:**
```bash
python ldap_admin.py user remove john.doe
```

#### Modify a User
```bash
python ldap_admin.py user modify <username> [--password <new_password>] [--attrs <json_attributes>]
```

**Examples:**
```bash
# Change password only
python ldap_admin.py user modify john.doe --password newpassword

# Update attributes (merge with existing)
python ldap_admin.py user modify john.doe --attrs '{"email": "john.doe@newcompany.com", "title": "Senior Engineer"}'

# Change password and attributes
python ldap_admin.py user modify john.doe --password newpass --attrs '{"phone": "+1234567890"}'

# Remove an attribute by setting it to null
python ldap_admin.py user modify john.doe --attrs '{"department": null}'
```

### Group Operations

#### Add a Group
```bash
python ldap_admin.py group add <group_name> [--members <username1> <username2> ...]
```

**Examples:**
```bash
# Empty group
python ldap_admin.py group add developers

# Group with initial members
python ldap_admin.py group add engineering --members john.doe jane.doe bob.smith
```

#### Remove a Group
```bash
python ldap_admin.py group remove <group_name>
```

**Example:**
```bash
python ldap_admin.py group remove oldteam
```

#### Modify Group Members
```bash
python ldap_admin.py group modify <group_name> [--add-members <username1> ...] [--remove-members <username1> ...]
```

**Examples:**
```bash
# Add members to group
python ldap_admin.py group modify developers --add-members alice.jones charlie.brown

# Remove members from group
python ldap_admin.py group modify developers --remove-members john.doe

# Add and remove members in one operation
python ldap_admin.py group modify engineering --add-members newuser --remove-members olduser
```

## Data Storage

The tool modifies JSON files in the `ldap-data/` directory:

### Users File (`ldap-data/users.json`)
```json
{
    "username": {
        "password": "plaintext_password",
        "email": "user@example.com",
        "cn": "Display Name",
        "department": "Engineering",
        "title": "Software Developer"
    }
}
```

### Groups File (`ldap-data/groups.json`)
```json
{
    "groupname": {
        "members": ["user1", "user2", "user3"]
    }
}
```

## Common Workflows

### Setting Up Initial Users
```bash
# Create admin user
python ldap_admin.py user add admin adminpass --attrs '{"cn": "Administrator", "email": "admin@company.com"}'

# Create regular users
python ldap_admin.py user add alice alicepass --attrs '{"cn": "Alice Smith", "email": "alice@company.com", "department": "Engineering"}'
python ldap_admin.py user add bob bobpass --attrs '{"cn": "Bob Jones", "email": "bob@company.com", "department": "Sales"}'
```

### Organizing Users into Groups
```bash
# Create department groups
python ldap_admin.py group add engineering --members alice
python ldap_admin.py group add sales --members bob
python ldap_admin.py group add administrators --members admin

# Create project-based groups
python ldap_admin.py group add project-alpha --members alice admin
```

### User Lifecycle Management
```bash
# New employee
python ldap_admin.py user add new.employee temppass --attrs '{"cn": "New Employee", "email": "new@company.com"}'
python ldap_admin.py group modify engineering --add-members new.employee

# Employee department change
python ldap_admin.py group modify engineering --remove-members alice
python ldap_admin.py group modify sales --add-members alice
python ldap_admin.py user modify alice --attrs '{"department": "Sales"}'

# Employee leaves
python ldap_admin.py group modify engineering --remove-members former.employee
python ldap_admin.py user remove former.employee
```

## Advanced Usage

### JSON Attributes

The `--attrs` parameter accepts a JSON string with user attributes. Common LDAP attributes include:

- `cn`: Common Name (display name)
- `email`: Email address
- `department`: Department/division
- `title`: Job title
- `phone`: Phone number
- `description`: Description or notes

**Complex attribute example:**
```bash
python ldap_admin.py user add complex.user password --attrs '{
    "cn": "Complex User",
    "email": "complex@company.com",
    "department": "Engineering",
    "title": "Senior Software Engineer",
    "phone": "+1-555-0123",
    "description": "Lead developer for project Alpha",
    "manager": "boss@company.com",
    "employeeId": "12345"
}'
```

### Bulk Operations

For bulk operations, you can use shell scripting:

```bash
# Add multiple users from a list
for user in alice bob charlie; do
    python ldap_admin.py user add $user defaultpass --attrs "{\"cn\": \"${user^}\", \"email\": \"$user@company.com\"}"
done

# Add all users to a group
python ldap_admin.py group modify everyone --add-members alice bob charlie
```

## Error Handling

The tool provides helpful error messages:

- **User/Group Not Found**: Clear messages when trying to modify non-existent entries
- **JSON Validation**: Warns about malformed JSON in attributes
- **File Permissions**: Reports issues accessing data files
- **Duplicate Entries**: Prevents creating users/groups that already exist

## Integration with LDAP Server

Changes made with the admin tool are immediately available to the LDAP server:

1. **No restart required**: The LDAP server reads JSON files for each operation
2. **Real-time updates**: Changes are visible immediately to LDAP clients
3. **Data validation**: The server handles malformed JSON gracefully

## Best Practices

1. **Use descriptive usernames**: Avoid spaces and special characters
2. **Set strong passwords**: The tool doesn't enforce password policies
3. **Include email attributes**: Many applications expect email addresses
4. **Organize with groups**: Use groups for access control and organization
5. **Regular backups**: Back up the `ldap-data/` directory regularly

## Security Considerations

⚠️ **Important Security Notes:**

- Passwords are stored in plaintext in JSON files
- Ensure proper file permissions on the `ldap-data/` directory
- Consider the security implications before using in production
- The tool requires direct filesystem access to the data files

## Troubleshooting

### File Permission Errors
```bash
# Check directory permissions
ls -la ldap-data/

# Fix permissions if needed
chmod 755 ldap-data/
chmod 644 ldap-data/*.json
```

### JSON Syntax Errors
- Use single quotes around the JSON string in shell commands
- Escape internal quotes properly
- Validate JSON syntax before running commands

### Missing Data Directory
The tool will automatically create the `ldap-data/` directory and empty JSON files if they don't exist.
