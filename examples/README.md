# Configuration Examples

This directory contains example configuration and setup files for the engineering tools.

## LDAP Server Configuration Examples

### Example Users and Groups

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

### Testing LDAP Connections

After setting up users, test the server with:

```bash
# Test authentication
ldapsearch -x -H ldap://localhost:389 -D "uid=alice,ou=users,dc=data-gadgets,dc=com" -w alicepass

# Search for a user
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(uid=alice)"

# List all users (requires admin privileges in some setups)
ldapsearch -x -H ldap://localhost:389 -b "ou=users,dc=data-gadgets,dc=com" "(objectClass=*)"
```

## Object Storage Configuration Examples

### Basic Server Setup

Start the object storage server with default settings:

```bash
# Start with HTTPS (recommended)
python object_storage_server.py

# Start with custom port and storage location
python object_storage_server.py --port 9000 --storage-path ./my-storage

# Start for local network access
python object_storage_server.py --host 0.0.0.0 --port 8443
```

### Client Usage Examples

```bash
# Health check
python object_storage_client.py health

# Create and manage buckets
python object_storage_client.py create-bucket photos
python object_storage_client.py create-bucket documents
python object_storage_client.py list-buckets

# Upload files
python object_storage_client.py upload vacation.jpg photos
python object_storage_client.py upload report.pdf documents --key reports/quarterly.pdf

# Download files
python object_storage_client.py download photos vacation.jpg
python object_storage_client.py download documents reports/quarterly.pdf --output ./downloads/report.pdf

# Sync directories
python object_storage_client.py sync ./photo-collection photos --prefix albums/
python object_storage_client.py sync ./documents documents --exclude "*.tmp" --exclude ".DS_Store"
```

### iOS/macOS Integration

**Connect iOS Files App:**
1. Open Files app on iOS
2. Tap "..." then "Connect to Server"
3. Enter server URL: `https://your-server-ip:8443/webdav/`
4. Accept certificate warning (self-signed)
5. Browse buckets as folders

**Connect macOS Finder:**
1. Open Finder, press Cmd+K
2. Enter: `https://your-server-ip:8443/webdav/`
3. Accept certificate warning
4. Mount as network drive

### AWS CLI Integration

Configure AWS CLI to work with the object storage server:

```bash
# Configure credentials
aws configure set aws_access_key_id AKIAIOSFODNN7EXAMPLE
aws configure set aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws configure set default.region us-east-1

# Use with the server
aws s3 ls --endpoint-url https://localhost:8443 --no-verify-ssl
aws s3 cp file.txt s3://my-bucket/ --endpoint-url https://localhost:8443 --no-verify-ssl
aws s3 sync ./folder s3://my-bucket/folder/ --endpoint-url https://localhost:8443 --no-verify-ssl
```

## Integration Examples

Both tools can be integrated with various applications that support their respective protocols:

### LDAP Integration
- Web applications for user authentication
- Email servers for address books
- VPN systems for user validation
- Network attached storage for access control

### Object Storage Integration
- Backup software (using S3-compatible APIs)
- Photo management apps (via WebDAV)
- Development tools (artifact storage)
- Content management systems
- Mobile apps (direct file upload/download)

## Production Considerations

### Security
- Change default access keys for object storage
- Use proper SSL certificates (not self-signed) in production
- Implement proper authentication and authorization
- Consider network segmentation and firewall rules

### Performance
- Use SSD storage for better I/O performance
- Monitor disk space and implement cleanup policies
- Consider load balancing for high availability
- Implement proper backup strategies

### Monitoring
- Monitor server health endpoints
- Set up log rotation and analysis
- Track storage usage and growth
- Monitor network bandwidth usage
