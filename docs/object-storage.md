# Object Storage Server & Client

A high-performance, multi-protocol object storage server with comprehensive client tools. Supports S3, Azure Blob Storage, Google Cloud Storage APIs, and WebDAV for seamless integration with various applications and mobile devices.

## Features

### Server Features
- **Multi-Protocol Support**: S3, Azure Blob, Google Cloud Storage, WebDAV APIs
- **HTTPS with Self-Signed Certificates**: Secure encrypted connections
- **HTTP Compression**: GZIP compression for faster transfers
- **Resumable Uploads/Downloads**: Range request support for large files
- **Mobile Device Support**: WebDAV protocol for iOS/macOS integration
- **Metadata Management**: Rich metadata storage and retrieval
- **Health Monitoring**: Built-in health check endpoints
- **CORS Support**: Cross-origin resource sharing for web applications

### Client Features
- **Easy File Management**: Upload, download, list, delete operations
- **Resume Capability**: Automatic resume for interrupted transfers
- **Progress Tracking**: Visual progress bars for large file operations
- **Directory Synchronization**: Bulk upload/sync of entire directories
- **Multiple Protocols**: Uses the most efficient protocol for each operation
- **SSL Certificate Handling**: Automatic handling of self-signed certificates

## Quick Start

### Prerequisites

Install required Python packages:

```bash
pip install flask requests urllib3 cryptography
```

### Starting the Server

```bash
# Start with default settings (HTTPS on port 8443)
python object_storage_server.py

# Start with custom settings
python object_storage_server.py --host 0.0.0.0 --port 9000 --storage-path ./my-storage

# Start without SSL (not recommended)
python object_storage_server.py --no-ssl --port 8080
```

Server will be available at:
- **S3 API**: `https://localhost:8443/`
- **Azure Blob API**: `https://localhost:8443/azure/`
- **Google Cloud Storage API**: `https://localhost:8443/gcs/`
- **WebDAV (iOS/macOS)**: `https://localhost:8443/webdav/`
- **Health Check**: `https://localhost:8443/health`

### Using the Client

```bash
# Check server health
python object_storage_client.py health

# Create a bucket
python object_storage_client.py create-bucket my-photos

# Upload a file
python object_storage_client.py upload photo.jpg my-photos

# Upload with custom key
python object_storage_client.py upload document.pdf my-docs --key documents/important.pdf

# List buckets
python object_storage_client.py list-buckets

# List objects in bucket
python object_storage_client.py list-objects my-photos

# Download a file
python object_storage_client.py download my-photos photo.jpg

# Download to specific location
python object_storage_client.py download my-photos photo.jpg --output ./downloads/photo.jpg

# Sync entire directory
python object_storage_client.py sync ./my-photos-folder my-photos --prefix photos/

# Delete an object
python object_storage_client.py delete my-photos photo.jpg

# Delete a bucket
python object_storage_client.py delete-bucket my-photos
```

## iOS/macOS Integration

### Using WebDAV

The server supports WebDAV protocol for native iOS and macOS integration:

**iOS (Files app):**
1. Open Files app
2. Tap "..." → "Connect to Server"
3. Enter: `https://your-server-ip:8443/webdav/`
4. Ignore certificate warnings (self-signed)
5. Access your buckets as folders

**macOS (Finder):**
1. Open Finder
2. Press Cmd+K
3. Enter: `https://your-server-ip:8443/webdav/`
4. Ignore certificate warnings
5. Mount as network drive

### iOS Shortcuts Integration

Create iOS shortcuts to automate uploads:

```javascript
// Example iOS Shortcut action
POST https://your-server:8443/bucket-name/file-name
Headers: Content-Type: image/jpeg
Body: [Photo from camera]
```

## API Documentation

### S3 Compatible API

#### List Buckets
```bash
GET /
```

#### Create Bucket
```bash
PUT /bucket-name
```

#### List Objects
```bash
GET /bucket-name?prefix=folder/
```

#### Upload Object
```bash
PUT /bucket-name/object-key
Content-Type: application/octet-stream
Body: [file data]
```

#### Download Object
```bash
GET /bucket-name/object-key
Range: bytes=0-1023  # Optional for partial downloads
```

#### Delete Object
```bash
DELETE /bucket-name/object-key
```

### Azure Blob Compatible API

#### Container Operations
```bash
GET /azure/container-name     # List blobs
PUT /azure/container-name     # Create container
DELETE /azure/container-name  # Delete container
```

#### Blob Operations
```bash
GET /azure/container-name/blob-name     # Download blob
PUT /azure/container-name/blob-name     # Upload blob
DELETE /azure/container-name/blob-name  # Delete blob
```

### Google Cloud Storage Compatible API

#### List Buckets
```bash
GET /gcs/storage/v1/b
```

#### List Objects
```bash
GET /gcs/storage/v1/b/bucket-name/o
```

#### Object Operations
```bash
GET /gcs/storage/v1/b/bucket-name/o/object-name?alt=media  # Download
PUT /gcs/storage/v1/b/bucket-name/o/object-name            # Upload
DELETE /gcs/storage/v1/b/bucket-name/o/object-name         # Delete
```

### WebDAV API

#### Directory Listing
```bash
PROPFIND /webdav/bucket-name/
```

#### File Operations
```bash
GET /webdav/bucket-name/file.txt      # Download
PUT /webdav/bucket-name/file.txt      # Upload
DELETE /webdav/bucket-name/file.txt   # Delete
MKCOL /webdav/new-bucket/             # Create directory
```

## Advanced Usage

### Custom Server Configuration

```python
from object_storage_server import ObjectStorageServer

# Create server with custom settings
server = ObjectStorageServer(
    storage_path='./custom-storage',
    metadata_path='./custom-metadata'
)

# Run with custom host/port
server.run(host='192.168.1.100', port=9443, debug=False)
```

### Client Configuration

```python
from object_storage_client import ObjectStorageClient

# Create client with custom settings
client = ObjectStorageClient(
    base_url='https://192.168.1.100:9443',
    access_key='your-access-key',
    secret_key='your-secret-key',
    verify_ssl=False,  # For self-signed certificates
    timeout=60
)

# Use programmatically
buckets = client.list_buckets()
client.upload_file('local-file.txt', 'my-bucket', 'remote-file.txt')
```

### Bulk Operations

```bash
# Sync directory with exclusions
python object_storage_client.py sync ./photos my-photos \
    --exclude "*.tmp" --exclude ".DS_Store" --exclude "__pycache__"

# Upload multiple files with pattern
for file in *.jpg; do
    python object_storage_client.py upload "$file" photos --key "gallery/$file"
done
```

### Integration with Third-Party Tools

#### AWS CLI (S3 Compatible)
```bash
# Configure AWS CLI to use your server
aws configure set aws_access_key_id AKIAIOSFODNN7EXAMPLE
aws configure set aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws configure set default.region us-east-1

# Use with custom endpoint
aws s3 ls --endpoint-url https://localhost:8443 --no-verify-ssl
aws s3 cp file.txt s3://my-bucket/ --endpoint-url https://localhost:8443 --no-verify-ssl
```

#### rclone Configuration
```ini
[object-storage]
type = s3
provider = Other
access_key_id = AKIAIOSFODNN7EXAMPLE
secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
endpoint = https://localhost:8443
no_check_bucket = true
```

## Performance Optimization

### Server Optimization
- **Storage Location**: Use SSD storage for better performance
- **Network**: Use wired connection for stability
- **Memory**: Allocate sufficient RAM for caching
- **Concurrency**: Server handles multiple simultaneous connections

### Client Optimization
- **Chunk Size**: Automatically optimized for file size
- **Compression**: Automatic GZIP compression for text files
- **Resume**: Automatic resume for interrupted transfers
- **Parallel Uploads**: Use multiple client instances for parallel uploads

### Transfer Speed Tips
1. **Use wired network connection** when possible
2. **Close unnecessary applications** during large transfers
3. **Use resume feature** for large files
4. **Monitor progress** with built-in progress bars
5. **Compress files** before upload for better transfer speeds

## Security Considerations

### SSL/TLS Security
- Server uses self-signed certificates by default
- Certificates are automatically generated on first run
- Certificates include localhost and local IP addresses
- Production use should implement proper CA-signed certificates

### Access Control
- Default access keys provided (change for production)
- No built-in user authentication (add middleware for production)
- CORS enabled for web application integration
- File system permissions protect stored data

### Network Security
- HTTPS encryption for all data transfers
- Client ignores certificate warnings for self-signed certificates
- All APIs require proper authentication headers
- Rate limiting can be added for production use

## Troubleshooting

### Server Issues

**Port Permission Denied**
```bash
# Use higher port number
python object_storage_server.py --port 8443

# Or run with sudo (not recommended)
sudo python object_storage_server.py --port 443
```

**Certificate Generation Failed**
```bash
# Install cryptography package
pip install cryptography

# Or run without SSL
python object_storage_server.py --no-ssl --port 8080
```

**Storage Path Issues**
```bash
# Specify custom storage path
python object_storage_server.py --storage-path /path/to/storage
```

### Client Issues

**SSL Certificate Verification**
```bash
# Disable SSL verification for self-signed certificates
python object_storage_client.py --no-ssl-verify health
```

**Connection Timeout**
```bash
# Use different server URL
python object_storage_client.py --server https://192.168.1.100:8443 health
```

**Upload/Download Failures**
```bash
# Use resume capability
python object_storage_client.py upload large-file.zip my-bucket
# Resume will happen automatically on retry
```

### iOS/macOS WebDAV Issues

**Certificate Trust Issues**
1. Safari: Visit `https://server-ip:8443/health`
2. Accept certificate warning
3. iOS Settings → General → About → Certificate Trust Settings
4. Enable trust for the certificate

**Connection Problems**
1. Ensure server is accessible from device
2. Check firewall settings
3. Try HTTP instead of HTTPS for testing
4. Verify WebDAV URL format

## File Structure

```
object-storage/           # Object storage data
├── bucket1/
│   ├── file1.txt
│   └── folder/
│       └── file2.jpg
└── bucket2/
    └── document.pdf

object-storage-metadata/  # Object metadata
├── bucket1_file1.txt.json
├── bucket1_folder_file2.jpg.json
└── bucket2_document.pdf.json

certs/                   # SSL certificates
├── server.crt
└── server.key

logs/                    # Server logs (if implemented)
└── object_storage.log
```

## Best Practices

### Server Management
1. **Regular Backups**: Backup both storage and metadata directories
2. **Monitor Disk Space**: Ensure adequate storage space
3. **Log Rotation**: Implement log rotation for production
4. **Security Updates**: Keep Python and dependencies updated
5. **Access Control**: Implement proper authentication for production

### Client Usage
1. **Use Resume**: Always enable resume for large files
2. **Progress Monitoring**: Monitor progress for long transfers
3. **Error Handling**: Check return codes and handle errors
4. **Batch Operations**: Use sync for multiple files
5. **Cleanup**: Regular cleanup of temporary files

### Integration
1. **API Selection**: Choose the most appropriate API for your use case
2. **Error Handling**: Implement proper error handling and retries
3. **Monitoring**: Monitor server health and performance
4. **Testing**: Test with self-signed certificates before production
5. **Documentation**: Document your specific configuration and usage

## Production Deployment

For production deployment, consider:

1. **Proper SSL Certificates**: Use CA-signed certificates
2. **Authentication**: Implement user authentication and authorization
3. **Rate Limiting**: Add rate limiting and abuse prevention
4. **Monitoring**: Add comprehensive logging and monitoring
5. **Backup Strategy**: Implement automated backup procedures
6. **Load Balancing**: Use load balancers for high availability
7. **Database Backend**: Consider database-backed metadata storage
8. **Compliance**: Ensure compliance with relevant regulations
