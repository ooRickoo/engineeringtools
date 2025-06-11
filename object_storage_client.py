#!/usr/bin/env python3
"""
Object Storage Client
Easy-to-use client for managing files with the Object Storage Server.
Supports upload, download, list, delete operations with resume capability.
"""

import os
import sys
import json
import hashlib
import mimetypes
import urllib3
import argparse
import gzip
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ObjectStorageClient:
    def __init__(self, 
                 base_url: str = "https://localhost:8443",
                 access_key: str = "AKIAIOSFODNN7EXAMPLE",
                 secret_key: str = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                 verify_ssl: bool = False,
                 timeout: int = 30):
        
        self.base_url = base_url.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Setup session with retry strategy
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configure session
        self.session.verify = verify_ssl
        self.session.timeout = timeout
        
        # Add compression support
        self.session.headers.update({
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'ObjectStorageClient/1.0'
        })

    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = urljoin(self.base_url, path)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all buckets"""
        try:
            response = self._make_request('GET', '/')
            
            # Parse S3-style XML response
            root = ET.fromstring(response.text)
            buckets = []
            
            for bucket_elem in root.findall('.//Bucket'):
                name_elem = bucket_elem.find('Name')
                date_elem = bucket_elem.find('CreationDate')
                
                if name_elem is not None:
                    buckets.append({
                        'name': name_elem.text,
                        'creation_date': date_elem.text if date_elem is not None else 'Unknown'
                    })
            
            return buckets
            
        except Exception as e:
            print(f"Error listing buckets: {e}")
            return []

    def create_bucket(self, bucket_name: str) -> bool:
        """Create a new bucket"""
        try:
            self._make_request('PUT', f'/{bucket_name}')
            print(f"Created bucket: {bucket_name}")
            return True
        except Exception as e:
            print(f"Error creating bucket {bucket_name}: {e}")
            return False

    def delete_bucket(self, bucket_name: str) -> bool:
        """Delete a bucket"""
        try:
            self._make_request('DELETE', f'/{bucket_name}')
            print(f"Deleted bucket: {bucket_name}")
            return True
        except Exception as e:
            print(f"Error deleting bucket {bucket_name}: {e}")
            return False

    def list_objects(self, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """List objects in a bucket"""
        try:
            params = {}
            if prefix:
                params['prefix'] = prefix
            
            response = self._make_request('GET', f'/{bucket_name}', params=params)
            
            # Parse S3-style XML response
            root = ET.fromstring(response.text)
            objects = []
            
            for contents in root.findall('.//Contents'):
                key_elem = contents.find('Key')
                size_elem = contents.find('Size')
                modified_elem = contents.find('LastModified')
                etag_elem = contents.find('ETag')
                
                if key_elem is not None:
                    size = int(size_elem.text) if size_elem is not None else 0
                    objects.append({
                        'key': key_elem.text,
                        'size': size,
                        'size_human': self._format_size(size),
                        'last_modified': modified_elem.text if modified_elem is not None else 'Unknown',
                        'etag': etag_elem.text.strip('"') if etag_elem is not None else 'Unknown'
                    })
            
            return objects
            
        except Exception as e:
            print(f"Error listing objects in bucket {bucket_name}: {e}")
            return []

    def upload_file(self, local_path: str, bucket_name: str, object_key: str = None, 
                   show_progress: bool = True, resume: bool = True) -> bool:
        """Upload a file to the storage server"""
        local_file = Path(local_path)
        
        if not local_file.exists():
            print(f"File not found: {local_path}")
            return False
        
        if object_key is None:
            object_key = local_file.name
        
        file_size = local_file.stat().st_size
        
        # Check if file already exists and has same content
        if resume:
            try:
                response = self._make_request('HEAD', f'/{bucket_name}/{quote(object_key)}')
                remote_size = int(response.headers.get('Content-Length', 0))
                remote_etag = response.headers.get('ETag', '').strip('"')
                
                if remote_size == file_size:
                    local_md5 = self._calculate_md5(local_file)
                    if local_md5 == remote_etag:
                        print(f"File {object_key} already exists with same content, skipping upload")
                        return True
            except:
                pass  # File doesn't exist, continue with upload
        
        try:
            print(f"Uploading {local_path} -> {bucket_name}/{object_key} ({self._format_size(file_size)})")
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(str(local_file))
            if not content_type:
                content_type = 'application/octet-stream'
            
            headers = {
                'Content-Type': content_type,
                'Content-Length': str(file_size)
            }
            
            # Upload with progress tracking
            with open(local_file, 'rb') as f:
                if show_progress and file_size > 1024 * 1024:  # Show progress for files > 1MB
                    self._upload_with_progress(f, bucket_name, object_key, headers, file_size)
                else:
                    response = self._make_request('PUT', f'/{bucket_name}/{quote(object_key)}', 
                                                data=f, headers=headers)
            
            print(f"Successfully uploaded {object_key}")
            return True
            
        except Exception as e:
            print(f"Error uploading {local_path}: {e}")
            return False

    def _upload_with_progress(self, file_obj, bucket_name: str, object_key: str, 
                            headers: Dict[str, str], total_size: int):
        """Upload file with progress indication"""
        chunk_size = 8192
        uploaded = 0
        
        def progress_generator():
            nonlocal uploaded
            while True:
                chunk = file_obj.read(chunk_size)
                if not chunk:
                    break
                uploaded += len(chunk)
                
                # Show progress
                percent = (uploaded / total_size) * 100
                bar_length = 50
                filled_length = int(bar_length * uploaded // total_size)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f'\rProgress: |{bar}| {percent:.1f}% ({self._format_size(uploaded)}/{self._format_size(total_size)})', end='')
                
                yield chunk
            print()  # New line after progress bar
        
        response = self._make_request('PUT', f'/{bucket_name}/{quote(object_key)}', 
                                    data=progress_generator(), headers=headers)

    def download_file(self, bucket_name: str, object_key: str, local_path: str = None, 
                     show_progress: bool = True, resume: bool = True) -> bool:
        """Download a file from the storage server"""
        if local_path is None:
            local_path = object_key.split('/')[-1]
        
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get file info
            head_response = self._make_request('HEAD', f'/{bucket_name}/{quote(object_key)}')
            remote_size = int(head_response.headers.get('Content-Length', 0))
            remote_etag = head_response.headers.get('ETag', '').strip('"')
            
            # Check if file already exists
            resume_pos = 0
            if resume and local_file.exists():
                local_size = local_file.stat().st_size
                if local_size == remote_size:
                    # Check if content matches
                    local_md5 = self._calculate_md5(local_file)
                    if local_md5 == remote_etag:
                        print(f"File {local_path} already exists with same content, skipping download")
                        return True
                elif local_size < remote_size:
                    resume_pos = local_size
                    print(f"Resuming download from position {self._format_size(resume_pos)}")
            
            print(f"Downloading {bucket_name}/{object_key} -> {local_path} ({self._format_size(remote_size)})")
            
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            response = self._make_request('GET', f'/{bucket_name}/{quote(object_key)}', 
                                        headers=headers, stream=True)
            
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(local_file, mode) as f:
                if show_progress and remote_size > 1024 * 1024:  # Show progress for files > 1MB
                    self._download_with_progress(response, f, remote_size, resume_pos)
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            print(f"Successfully downloaded {object_key}")
            return True
            
        except Exception as e:
            print(f"Error downloading {object_key}: {e}")
            return False

    def _download_with_progress(self, response, file_obj, total_size: int, start_pos: int = 0):
        """Download file with progress indication"""
        downloaded = start_pos
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_obj.write(chunk)
                downloaded += len(chunk)
                
                # Show progress
                percent = (downloaded / total_size) * 100
                bar_length = 50
                filled_length = int(bar_length * downloaded // total_size)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                print(f'\rProgress: |{bar}| {percent:.1f}% ({self._format_size(downloaded)}/{self._format_size(total_size)})', end='')
        
        print()  # New line after progress bar

    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """Delete an object"""
        try:
            self._make_request('DELETE', f'/{bucket_name}/{quote(object_key)}')
            print(f"Deleted object: {bucket_name}/{object_key}")
            return True
        except Exception as e:
            print(f"Error deleting object {bucket_name}/{object_key}: {e}")
            return False

    def sync_directory(self, local_dir: str, bucket_name: str, prefix: str = '', 
                      exclude_patterns: List[str] = None) -> bool:
        """Sync a local directory to a bucket"""
        local_path = Path(local_dir)
        if not local_path.exists() or not local_path.is_dir():
            print(f"Directory not found: {local_dir}")
            return False
        
        exclude_patterns = exclude_patterns or ['.DS_Store', '__pycache__', '*.pyc', '.git']
        
        def should_exclude(file_path: Path) -> bool:
            for pattern in exclude_patterns:
                if pattern in str(file_path) or file_path.name == pattern:
                    return True
            return False
        
        print(f"Syncing directory {local_dir} to bucket {bucket_name}")
        
        success_count = 0
        error_count = 0
        
        for file_path in local_path.rglob('*'):
            if file_path.is_file() and not should_exclude(file_path):
                relative_path = file_path.relative_to(local_path)
                object_key = f"{prefix}{relative_path}".replace('\\', '/')  # Normalize path separators
                
                if self.upload_file(str(file_path), bucket_name, object_key, show_progress=False):
                    success_count += 1
                else:
                    error_count += 1
        
        print(f"Sync completed: {success_count} files uploaded, {error_count} errors")
        return error_count == 0

    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        try:
            response = self._make_request('GET', '/health')
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return {'status': 'error', 'message': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Object Storage Client')
    parser.add_argument('--server', default='https://localhost:8443', help='Server URL')
    parser.add_argument('--access-key', default='AKIAIOSFODNN7EXAMPLE', help='Access key')
    parser.add_argument('--secret-key', default='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY', help='Secret key')
    parser.add_argument('--ssl-verify', action='store_true', help='Enable SSL verification (default: disabled for self-signed certs)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List buckets
    subparsers.add_parser('list-buckets', help='List all buckets')
    
    # Create bucket
    create_bucket_parser = subparsers.add_parser('create-bucket', help='Create a bucket')
    create_bucket_parser.add_argument('bucket', help='Bucket name')
    
    # Delete bucket
    delete_bucket_parser = subparsers.add_parser('delete-bucket', help='Delete a bucket')
    delete_bucket_parser.add_argument('bucket', help='Bucket name')
    
    # List objects
    list_objects_parser = subparsers.add_parser('list-objects', help='List objects in a bucket')
    list_objects_parser.add_argument('bucket', help='Bucket name')
    list_objects_parser.add_argument('--prefix', default='', help='Object prefix filter')
    
    # Upload file
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('file', help='Local file path')
    upload_parser.add_argument('bucket', help='Bucket name')
    upload_parser.add_argument('--key', help='Object key (default: filename)')
    upload_parser.add_argument('--no-resume', action='store_true', help='Disable resume')
    
    # Download file
    download_parser = subparsers.add_parser('download', help='Download a file')
    download_parser.add_argument('bucket', help='Bucket name')
    download_parser.add_argument('key', help='Object key')
    download_parser.add_argument('--output', help='Output file path (default: object key)')
    download_parser.add_argument('--no-resume', action='store_true', help='Disable resume')
    
    # Delete object
    delete_parser = subparsers.add_parser('delete', help='Delete an object')
    delete_parser.add_argument('bucket', help='Bucket name')
    delete_parser.add_argument('key', help='Object key')
    
    # Sync directory
    sync_parser = subparsers.add_parser('sync', help='Sync directory to bucket')
    sync_parser.add_argument('directory', help='Local directory')
    sync_parser.add_argument('bucket', help='Bucket name')
    sync_parser.add_argument('--prefix', default='', help='Object key prefix')
    sync_parser.add_argument('--exclude', action='append', help='Exclude patterns')
    
    # Health check
    subparsers.add_parser('health', help='Check server health')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize client
    client = ObjectStorageClient(
        base_url=args.server,
        access_key=args.access_key,
        secret_key=args.secret_key,
        verify_ssl=args.ssl_verify
    )
    
    # Execute command
    if args.command == 'list-buckets':
        buckets = client.list_buckets()
        if buckets:
            print(f"{'Bucket Name':<30} {'Creation Date':<25}")
            print("-" * 55)
            for bucket in buckets:
                print(f"{bucket['name']:<30} {bucket['creation_date']:<25}")
        else:
            print("No buckets found")
    
    elif args.command == 'create-bucket':
        client.create_bucket(args.bucket)
    
    elif args.command == 'delete-bucket':
        client.delete_bucket(args.bucket)
    
    elif args.command == 'list-objects':
        objects = client.list_objects(args.bucket, args.prefix)
        if objects:
            print(f"{'Object Key':<50} {'Size':<15} {'Last Modified':<25}")
            print("-" * 90)
            for obj in objects:
                print(f"{obj['key']:<50} {obj['size_human']:<15} {obj['last_modified']:<25}")
        else:
            print(f"No objects found in bucket {args.bucket}")
    
    elif args.command == 'upload':
        client.upload_file(args.file, args.bucket, args.key, resume=not args.no_resume)
    
    elif args.command == 'download':
        client.download_file(args.bucket, args.key, args.output, resume=not args.no_resume)
    
    elif args.command == 'delete':
        client.delete_object(args.bucket, args.key)
    
    elif args.command == 'sync':
        exclude_patterns = args.exclude or []
        client.sync_directory(args.directory, args.bucket, args.prefix, exclude_patterns)
    
    elif args.command == 'health':
        health = client.health_check()
        print(json.dumps(health, indent=2))


if __name__ == '__main__':
    main()
