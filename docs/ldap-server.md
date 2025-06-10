# LDAP Server

A lightweight, Python-based LDAP server built with Twisted and ldaptor that provides basic LDAP authentication and search functionality with JSON-based data persistence.

## Features

- **Standard LDAP Protocol**: Runs on port 389 (configurable)
- **JSON Data Storage**: User and group data stored in human-readable JSON files
- **Log Rotation**: Automatic log rotation with configurable size limits
- **Basic Authentication**: Supports LDAP bind operations for user authentication
- **Search Operations**: Basic search functionality for users and groups
- **Configurable Base DN**: Default `ou=users,dc=data-gadgets,dc=com`

## Requirements

- Python 3.7+
- Twisted
- ldaptor

## Installation

1. Install dependencies:
   ```bash
   pip install twisted ldaptor
   ```

2. The server will automatically create necessary directories and files on first run.

## Usage

### Starting the Server

```bash
python ldap_server.py
```

The server will:
- Create `ldap-data/` directory for JSON data files
- Create `logs/` directory for log files
- Start listening on port 389
- Use base DN: `ou=users,dc=data-gadgets,dc=com`

### Configuration

You can modify the following in `ldap_server.py`:

- **Port**: Change `port = 389` in the `main()` function
- **Base DN**: Modify `base_dn_str` in the `MyLDAPServer` class
- **Log Settings**: Adjust `rotateLength` and `maxRotatedFiles` in the LogFile configuration

### Data Storage

User and group data is stored in JSON files:

- `ldap-data/users.json` - User accounts with passwords and attributes
- `ldap-data/groups.json` - Group definitions with member lists

#### User Data Format
```json
{
    "username": {
        "password": "plaintext_password",
        "email": "user@example.com",
        "cn": "Display Name",
        "custom_attribute": "value"
    }
}
```

#### Group Data Format
```json
{
    "groupname": {
        "members": ["user1", "user2", "user3"]
    }
}
```

### LDAP Client Configuration

When connecting with LDAP clients:

- **Host**: localhost (or your server IP)
- **Port**: 389
- **Base DN**: `ou=users,dc=data-gadgets,dc=com`
- **User DN Format**: `uid=<username>,ou=users,dc=data-gadgets,dc=com`

### Example LDAP Operations

#### Binding (Authentication)
```bash
ldapsearch -x -H ldap://localhost:389 -D "uid=testuser,ou=users,dc=data-gadgets,dc=com" -w password
```

#### Searching for Users
```bash
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(uid=testuser)"
```

#### Listing All Users
```bash
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(objectClass=*)"
```

## Logging

Logs are stored in the `logs/` directory with automatic rotation:

- **File**: `logs/ldap_server.log`
- **Max Size**: 10MB per file
- **Retention**: 5 rotated files (50MB total)

## Security Considerations

⚠️ **Important**: This is a basic LDAP server intended for development/testing purposes.

- Passwords are stored in plaintext in JSON files
- No encryption for LDAP connections (LDAPS not implemented)
- Basic access controls only
- Not recommended for production environments without additional security measures

## Troubleshooting

### Permission Denied on Port 389
If you get permission errors on port 389, either:
1. Run with sudo: `sudo python ldap_server.py`
2. Change to a higher port (e.g., 3890) in the code

### Port Already in Use
Kill existing processes: `pkill -f "python ldap_server.py"`

### JSON File Corruption
If JSON files become corrupted, delete them - the server will recreate empty ones on restart.

## Architecture

The server consists of:

- **MyLDAPServer**: Main server class handling LDAP protocol operations
- **MyLDAPEntry**: LDAP entry representation with bind capabilities  
- **JSON Data Layer**: Simple file-based storage using `load_data()` and `save_data()`
- **Twisted Framework**: Asynchronous networking and logging

## Limitations

- Basic search filters only (uid-based searches)
- No LDAP modify operations (use ldap_admin.py instead)
- No SSL/TLS support
- No access control lists (ACLs)
- Single base DN support
