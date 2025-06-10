# LDAP Server Configuration Examples

This directory contains example configuration and setup files for the LDAP server.

## Example Users and Groups

You can use the LDAP admin tool to create these example users and groups:

```bash
# Create example users
python ldap_admin.py user add admin adminpass --attrs '{"cn": "Administrator", "email": "admin@company.com", "title": "System Administrator"}'
python ldap_admin.py user add alice alicepass --attrs '{"cn": "Alice Smith", "email": "alice@company.com", "department": "Engineering", "title": "Software Engineer"}'
python ldap_admin.py user add bob bobpass --attrs '{"cn": "Bob Jones", "email": "bob@company.com", "department": "Sales", "title": "Sales Manager"}'

# Create example groups
python ldap_admin.py group add administrators --members admin
python ldap_admin.py group add engineering --members alice
python ldap_admin.py group add sales --members bob
python ldap_admin.py group add all-users --members admin alice bob
```

## Testing LDAP Connections

After setting up users, test the server with:

```bash
# Test authentication
ldapsearch -x -H ldap://localhost:389 -D "uid=alice,ou=users,dc=data-gadgets,dc=com" -w alicepass

# Search for a user
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(uid=alice)"

# List all users (requires admin privileges in some setups)
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(objectClass=*)"
```

## Integration Examples

The LDAP server can be integrated with various applications that support LDAP authentication. See the individual tool documentation for specific integration guides.
