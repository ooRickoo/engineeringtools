#!/bin/bash

# Quick Start Script for Object Storage Server
# This script demonstrates basic setup and usage

echo "🚀 Object Storage Server Quick Start"
echo "===================================="

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import flask, requests, urllib3, cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies are installed"
fi

echo ""
echo "🔧 Quick Setup Instructions:"
echo ""
echo "1. Start the server:"
echo "   python object_storage_server.py"
echo ""
echo "2. In another terminal, test the client:"
echo "   python object_storage_client.py health"
echo ""
echo "3. Create a test bucket:"
echo "   python object_storage_client.py create-bucket test-bucket"
echo ""
echo "4. Upload a file:"
echo "   echo 'Hello, World!' > test.txt"
echo "   python object_storage_client.py upload test.txt test-bucket"
echo ""
echo "5. List objects:"
echo "   python object_storage_client.py list-objects test-bucket"
echo ""
echo "6. Download the file:"
echo "   python object_storage_client.py download test-bucket test.txt --output downloaded.txt"
echo ""
echo "📱 iOS/macOS Integration:"
echo "   Connect to: https://localhost:8443/webdav/"
echo "   (Accept certificate warning for self-signed cert)"
echo ""
echo "🏥 Health Check:"
echo "   curl -k https://localhost:8443/health"
echo ""
echo "📚 Full documentation: docs/object-storage.md"
echo ""

# Offer to install dependencies if not present
read -p "Would you like to install dependencies now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"
fi

echo ""
echo "🎉 Ready to start! Run: python object_storage_server.py"
