#!/usr/bin/env python3
"""
Object Storage Server
A multi-protocol compatible object storage server with S3, Azure Blob, and Google Cloud Storage APIs.
Supports HTTPS with self-signed certificates, compression, and mobile-friendly protocols.
"""

import os
import json
import hashlib
import mimetypes
import gzip
import ssl
import time
import base64
import hmac
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import xml.etree.ElementTree as ET

from flask import Flask, request, Response, jsonify, send_file, abort
from werkzeug.serving import WSGIRequestHandler
from werkzeug.utils import secure_filename
import argparse

# Configuration
DEFAULT_PORT = 8443
DEFAULT_HOST = '0.0.0.0'
STORAGE_PATH = './object-storage'
METADATA_PATH = './object-storage-metadata'
CERT_PATH = './certs'
ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

class ObjectStorageServer:
    def __init__(self, storage_path: str = STORAGE_PATH, metadata_path: str = METADATA_PATH):
        self.app = Flask(__name__)
        self.storage_path = Path(storage_path)
        self.metadata_path = Path(metadata_path)
        
        # Create directories
        self.storage_path.mkdir(exist_ok=True)
        self.metadata_path.mkdir(exist_ok=True)
        
        # Setup routes
        self._setup_routes()
        
        # CORS headers for web compatibility
        @self.app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Range,x-amz-date,x-amz-content-sha256')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,HEAD,OPTIONS')
            response.headers.add('Access-Control-Expose-Headers', 'ETag,Content-Length,Content-Range,Accept-Ranges')
            return response

    def _setup_routes(self):
        """Setup all API routes for different protocols"""
        
        # S3 Compatible API
        self.app.add_url_rule('/', 'list_buckets', self.list_buckets, methods=['GET'])
        self.app.add_url_rule('/<bucket_name>', 'bucket_operations', self.bucket_operations, methods=['GET', 'PUT', 'DELETE', 'HEAD'])
        self.app.add_url_rule('/<bucket_name>/<path:object_key>', 'object_operations', self.object_operations, methods=['GET', 'PUT', 'DELETE', 'HEAD'])
        
        # Azure Blob Compatible API
        self.app.add_url_rule('/azure/<container_name>', 'azure_container', self.azure_container_operations, methods=['GET', 'PUT', 'DELETE'])
        self.app.add_url_rule('/azure/<container_name>/<path:blob_name>', 'azure_blob', self.azure_blob_operations, methods=['GET', 'PUT', 'DELETE', 'HEAD'])
        
        # Google Cloud Storage Compatible API
        self.app.add_url_rule('/gcs/storage/v1/b', 'gcs_list_buckets', self.gcs_list_buckets, methods=['GET'])
        self.app.add_url_rule('/gcs/storage/v1/b/<bucket_name>/o', 'gcs_list_objects', self.gcs_list_objects, methods=['GET'])
        self.app.add_url_rule('/gcs/storage/v1/b/<bucket_name>/o/<path:object_name>', 'gcs_object', self.gcs_object_operations, methods=['GET', 'PUT', 'DELETE'])
        
        # WebDAV for iOS/macOS compatibility
        self.app.add_url_rule('/webdav', 'webdav_root', self.webdav_root, methods=['PROPFIND', 'OPTIONS'])
        self.app.add_url_rule('/webdav/', 'webdav_root_slash', self.webdav_root, methods=['PROPFIND', 'OPTIONS'])
        self.app.add_url_rule('/webdav/<path:path>', 'webdav_operations', self.webdav_operations, methods=['GET', 'PUT', 'DELETE', 'PROPFIND', 'MKCOL', 'COPY', 'MOVE', 'OPTIONS'])
        
        # Health check
        self.app.add_url_rule('/health', 'health', self.health_check, methods=['GET'])
        
        # OPTIONS for CORS preflight
        self.app.add_url_rule('/<path:path>', 'options', self.handle_options, methods=['OPTIONS'])

    def _get_compressed_response(self, data: bytes, content_type: str = 'application/octet-stream') -> Response:
        """Create a compressed response if client supports it"""
        if 'gzip' in request.headers.get('Accept-Encoding', ''):
            compressed_data = gzip.compress(data)
            response = Response(compressed_data, content_type=content_type)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed_data)
        else:
            response = Response(data, content_type=content_type)
            response.headers['Content-Length'] = len(data)
        
        return response

    def _save_object(self, bucket: str, key: str, data: bytes, content_type: str = None) -> Dict[str, Any]:
        """Save object to storage with metadata"""
        bucket_path = self.storage_path / bucket
        bucket_path.mkdir(exist_ok=True)
        
        object_path = bucket_path / key
        object_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write data
        with open(object_path, 'wb') as f:
            f.write(data)
        
        # Calculate ETag (MD5 hash)
        etag = hashlib.md5(data).hexdigest()
        
        # Save metadata
        metadata = {
            'bucket': bucket,
            'key': key,
            'size': len(data),
            'etag': etag,
            'content_type': content_type or mimetypes.guess_type(key)[0] or 'application/octet-stream',
            'last_modified': datetime.utcnow().isoformat() + 'Z',
            'created': datetime.utcnow().isoformat() + 'Z'
        }
        
        metadata_file = self.metadata_path / f"{bucket}_{key.replace('/', '_')}.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        return metadata

    def _get_object_metadata(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """Get object metadata"""
        metadata_file = self.metadata_path / f"{bucket}_{key.replace('/', '_')}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None

    def _delete_object(self, bucket: str, key: str) -> bool:
        """Delete object and its metadata"""
        object_path = self.storage_path / bucket / key
        metadata_file = self.metadata_path / f"{bucket}_{key.replace('/', '_')}.json"
        
        deleted = False
        if object_path.exists():
            object_path.unlink()
            deleted = True
        
        if metadata_file.exists():
            metadata_file.unlink()
            deleted = True
        
        return deleted

    def _list_bucket_objects(self, bucket: str, prefix: str = '', delimiter: str = '') -> List[Dict[str, Any]]:
        """List objects in a bucket"""
        bucket_path = self.storage_path / bucket
        if not bucket_path.exists():
            return []
        
        objects = []
        for metadata_file in self.metadata_path.glob(f"{bucket}_*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if prefix and not metadata['key'].startswith(prefix):
                        continue
                    objects.append(metadata)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        return sorted(objects, key=lambda x: x['key'])

    # S3 Compatible API Handlers
    def list_buckets(self):
        """List all buckets (S3 API)"""
        buckets = []
        for bucket_dir in self.storage_path.iterdir():
            if bucket_dir.is_dir():
                buckets.append({
                    'Name': bucket_dir.name,
                    'CreationDate': datetime.fromtimestamp(bucket_dir.stat().st_ctime).isoformat() + 'Z'
                })
        
        # Return S3-style XML response
        root = ET.Element('ListAllMyBucketsResult')
        owner = ET.SubElement(root, 'Owner')
        ET.SubElement(owner, 'ID').text = 'object-storage-server'
        ET.SubElement(owner, 'DisplayName').text = 'Object Storage Server'
        
        buckets_elem = ET.SubElement(root, 'Buckets')
        for bucket in buckets:
            bucket_elem = ET.SubElement(buckets_elem, 'Bucket')
            ET.SubElement(bucket_elem, 'Name').text = bucket['Name']
            ET.SubElement(bucket_elem, 'CreationDate').text = bucket['CreationDate']
        
        xml_response = ET.tostring(root, encoding='unicode')
        return Response(xml_response, content_type='application/xml')

    def bucket_operations(self, bucket_name):
        """Handle bucket operations (S3 API)"""
        if request.method == 'GET':
            # List objects in bucket
            prefix = request.args.get('prefix', '')
            delimiter = request.args.get('delimiter', '')
            objects = self._list_bucket_objects(bucket_name, prefix, delimiter)
            
            # Return S3-style XML response
            root = ET.Element('ListBucketResult')
            ET.SubElement(root, 'Name').text = bucket_name
            ET.SubElement(root, 'Prefix').text = prefix
            ET.SubElement(root, 'MaxKeys').text = '1000'
            ET.SubElement(root, 'IsTruncated').text = 'false'
            
            for obj in objects:
                contents = ET.SubElement(root, 'Contents')
                ET.SubElement(contents, 'Key').text = obj['key']
                ET.SubElement(contents, 'LastModified').text = obj['last_modified']
                ET.SubElement(contents, 'ETag').text = f'"{obj["etag"]}"'
                ET.SubElement(contents, 'Size').text = str(obj['size'])
            
            xml_response = ET.tostring(root, encoding='unicode')
            return Response(xml_response, content_type='application/xml')
        
        elif request.method == 'PUT':
            # Create bucket
            bucket_path = self.storage_path / bucket_name
            bucket_path.mkdir(exist_ok=True)
            return Response('', status=200)
        
        elif request.method == 'DELETE':
            # Delete bucket
            bucket_path = self.storage_path / bucket_name
            if bucket_path.exists():
                import shutil
                shutil.rmtree(bucket_path)
            return Response('', status=204)

    def object_operations(self, bucket_name, object_key):
        """Handle object operations (S3 API)"""
        if request.method == 'GET':
            # Get object
            object_path = self.storage_path / bucket_name / object_key
            if not object_path.exists():
                abort(404)
            
            metadata = self._get_object_metadata(bucket_name, object_key)
            if not metadata:
                abort(404)
            
            # Handle range requests for resumable downloads
            range_header = request.headers.get('Range')
            if range_header:
                return self._handle_range_request(object_path, metadata, range_header)
            
            with open(object_path, 'rb') as f:
                data = f.read()
            
            response = self._get_compressed_response(data, metadata['content_type'])
            response.headers['ETag'] = f'"{metadata["etag"]}"'
            response.headers['Last-Modified'] = metadata['last_modified']
            response.headers['Accept-Ranges'] = 'bytes'
            
            return response
        
        elif request.method == 'PUT':
            # Put object
            data = request.get_data()
            content_type = request.headers.get('Content-Type', 'application/octet-stream')
            
            metadata = self._save_object(bucket_name, object_key, data, content_type)
            
            response = Response('', status=200)
            response.headers['ETag'] = f'"{metadata["etag"]}"'
            return response
        
        elif request.method == 'DELETE':
            # Delete object
            if self._delete_object(bucket_name, object_key):
                return Response('', status=204)
            else:
                abort(404)
        
        elif request.method == 'HEAD':
            # Head object
            metadata = self._get_object_metadata(bucket_name, object_key)
            if not metadata:
                abort(404)
            
            response = Response('', status=200)
            response.headers['Content-Length'] = str(metadata['size'])
            response.headers['Content-Type'] = metadata['content_type']
            response.headers['ETag'] = f'"{metadata["etag"]}"'
            response.headers['Last-Modified'] = metadata['last_modified']
            response.headers['Accept-Ranges'] = 'bytes'
            
            return response

    def _handle_range_request(self, object_path: Path, metadata: Dict, range_header: str) -> Response:
        """Handle HTTP range requests for partial content"""
        file_size = metadata['size']
        
        # Parse range header (e.g., "bytes=0-1023")
        try:
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            if start >= file_size or end >= file_size:
                abort(416)  # Range Not Satisfiable
            
            with open(object_path, 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)
            
            response = Response(data, status=206)  # Partial Content
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers['Content-Length'] = str(len(data))
            response.headers['Content-Type'] = metadata['content_type']
            response.headers['Accept-Ranges'] = 'bytes'
            
            return response
        
        except (ValueError, IndexError):
            abort(400)  # Bad Request

    # Azure Blob Compatible API
    def azure_container_operations(self, container_name):
        """Handle Azure Blob container operations"""
        return self.bucket_operations(container_name)

    def azure_blob_operations(self, container_name, blob_name):
        """Handle Azure Blob operations"""
        return self.object_operations(container_name, blob_name)

    # Google Cloud Storage Compatible API
    def gcs_list_buckets(self):
        """List buckets (GCS API)"""
        buckets = []
        for bucket_dir in self.storage_path.iterdir():
            if bucket_dir.is_dir():
                buckets.append({
                    'name': bucket_dir.name,
                    'timeCreated': datetime.fromtimestamp(bucket_dir.stat().st_ctime).isoformat() + 'Z'
                })
        
        return jsonify({'items': buckets})

    def gcs_list_objects(self, bucket_name):
        """List objects in bucket (GCS API)"""
        objects = self._list_bucket_objects(bucket_name)
        gcs_objects = []
        
        for obj in objects:
            gcs_objects.append({
                'name': obj['key'],
                'bucket': obj['bucket'],
                'size': str(obj['size']),
                'contentType': obj['content_type'],
                'etag': obj['etag'],
                'timeCreated': obj['created'],
                'updated': obj['last_modified']
            })
        
        return jsonify({'items': gcs_objects})

    def gcs_object_operations(self, bucket_name, object_name):
        """Handle GCS object operations"""
        if request.method == 'GET':
            alt = request.args.get('alt', 'json')
            if alt == 'media':
                return self.object_operations(bucket_name, object_name)
            else:
                # Return metadata
                metadata = self._get_object_metadata(bucket_name, object_name)
                if not metadata:
                    abort(404)
                
                return jsonify({
                    'name': metadata['key'],
                    'bucket': metadata['bucket'],
                    'size': str(metadata['size']),
                    'contentType': metadata['content_type'],
                    'etag': metadata['etag'],
                    'timeCreated': metadata['created'],
                    'updated': metadata['last_modified']
                })
        
        return self.object_operations(bucket_name, object_name)

    # WebDAV for iOS/macOS compatibility
    def webdav_root(self):
        """Handle WebDAV root operations"""
        if request.method == 'PROPFIND':
            # Return WebDAV directory listing
            return self._webdav_propfind('/')
        elif request.method == 'OPTIONS':
            response = Response('', status=200)
            response.headers['DAV'] = '1, 2'
            response.headers['Allow'] = 'OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK'
            return response

    def webdav_operations(self, path):
        """Handle WebDAV operations for iOS/macOS"""
        if request.method == 'PROPFIND':
            return self._webdav_propfind(path)
        elif request.method == 'GET':
            return self._webdav_get(path)
        elif request.method == 'PUT':
            return self._webdav_put(path)
        elif request.method == 'DELETE':
            return self._webdav_delete(path)
        elif request.method == 'MKCOL':
            return self._webdav_mkcol(path)
        # Add more WebDAV methods as needed

    def _webdav_propfind(self, path: str) -> Response:
        """Handle WebDAV PROPFIND requests"""
        # Simplified WebDAV response for directory listing
        webdav_xml = '''<?xml version="1.0" encoding="utf-8" ?>
<D:multistatus xmlns:D="DAV:">
<D:response>
<D:href>/webdav{}</D:href>
<D:propstat>
<D:prop>
<D:resourcetype><D:collection/></D:resourcetype>
<D:displayname>{}</D:displayname>
</D:prop>
<D:status>HTTP/1.1 200 OK</D:status>
</D:propstat>
</D:response>
</D:multistatus>'''.format(path, path.split('/')[-1] or 'root')
        
        return Response(webdav_xml, content_type='application/xml', status=207)

    def _webdav_get(self, path: str) -> Response:
        """Handle WebDAV GET requests"""
        # Map WebDAV path to storage
        parts = path.strip('/').split('/', 1)
        if len(parts) == 2:
            bucket, key = parts
            return self.object_operations(bucket, key)
        else:
            return self.bucket_operations(parts[0] if parts else '')

    def _webdav_put(self, path: str) -> Response:
        """Handle WebDAV PUT requests"""
        parts = path.strip('/').split('/', 1)
        if len(parts) == 2:
            bucket, key = parts
            return self.object_operations(bucket, key)
        abort(400)

    def _webdav_delete(self, path: str) -> Response:
        """Handle WebDAV DELETE requests"""
        parts = path.strip('/').split('/', 1)
        if len(parts) == 2:
            bucket, key = parts
            return self.object_operations(bucket, key)
        abort(400)

    def _webdav_mkcol(self, path: str) -> Response:
        """Handle WebDAV MKCOL requests (create collection/directory)"""
        bucket_name = path.strip('/')
        if '/' not in bucket_name:
            return self.bucket_operations(bucket_name)
        abort(400)

    def health_check(self):
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'object-storage-server',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'storage_path': str(self.storage_path),
            'protocols': ['S3', 'Azure Blob', 'Google Cloud Storage', 'WebDAV']
        })

    def handle_options(self, path):
        """Handle CORS preflight requests"""
        response = Response('', status=200)
        return response

    def create_self_signed_cert(self, cert_dir: Path):
        """Create self-signed SSL certificate"""
        cert_dir.mkdir(exist_ok=True)
        cert_file = cert_dir / 'server.crt'
        key_file = cert_dir / 'server.key'
        
        if cert_file.exists() and key_file.exists():
            return str(cert_file), str(key_file)
        
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import ipaddress
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Object Storage Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("*.local"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Write certificate
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write private key
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            print(f"Created self-signed certificate: {cert_file}")
            return str(cert_file), str(key_file)
            
        except ImportError:
            print("Warning: cryptography package not available. Install with: pip install cryptography")
            print("Falling back to HTTP mode (not recommended for production)")
            return None, None

    def run(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False, use_ssl: bool = True):
        """Run the server"""
        print(f"Starting Object Storage Server...")
        print(f"Storage path: {self.storage_path}")
        print(f"Metadata path: {self.metadata_path}")
        
        if use_ssl:
            cert_dir = Path(CERT_PATH)
            cert_file, key_file = self.create_self_signed_cert(cert_dir)
            
            if cert_file and key_file:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(cert_file, key_file)
                
                print(f"Server running with HTTPS on https://{host}:{port}")
                print("Protocols supported:")
                print(f"  - S3 API: https://{host}:{port}/")
                print(f"  - Azure Blob: https://{host}:{port}/azure/")
                print(f"  - Google Cloud Storage: https://{host}:{port}/gcs/")
                print(f"  - WebDAV (iOS/macOS): https://{host}:{port}/webdav/")
                print(f"  - Health check: https://{host}:{port}/health")
                
                self.app.run(host=host, port=port, debug=debug, ssl_context=context, threaded=True)
            else:
                print(f"Server running with HTTP on http://{host}:{port}")
                self.app.run(host=host, port=port, debug=debug, threaded=True)
        else:
            print(f"Server running with HTTP on http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    parser = argparse.ArgumentParser(description='Object Storage Server')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to bind to')
    parser.add_argument('--storage-path', default=STORAGE_PATH, help='Path to store objects')
    parser.add_argument('--metadata-path', default=METADATA_PATH, help='Path to store metadata')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL/HTTPS')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    server = ObjectStorageServer(args.storage_path, args.metadata_path)
    server.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_ssl=not args.no_ssl
    )


if __name__ == '__main__':
    main()
