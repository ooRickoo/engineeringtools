#!/bin/bash

# Object Storage Server Demo Script
# Demonstrates all major features of the object storage system

echo "🚀 Object Storage Server Demo"
echo "============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Step 1: Health Check${NC}"
python object_storage_client.py health
echo ""

echo -e "${BLUE}📋 Step 2: Create Demo Buckets${NC}"
python object_storage_client.py create-bucket demo-photos
python object_storage_client.py create-bucket demo-documents
echo ""

echo -e "${BLUE}📋 Step 3: List All Buckets${NC}"
python object_storage_client.py list-buckets
echo ""

echo -e "${BLUE}📋 Step 4: Create Test Files${NC}"
echo "This is a demo photo file" > demo-photo.txt
echo "This is a demo document" > demo-doc.pdf
echo "Configuration settings for demo" > config.json
echo -e "${GREEN}✅ Created test files${NC}"
echo ""

echo -e "${BLUE}📋 Step 5: Upload Individual Files${NC}"
python object_storage_client.py upload demo-photo.txt demo-photos --key photos/vacation.txt
python object_storage_client.py upload demo-doc.pdf demo-documents --key documents/report.pdf
python object_storage_client.py upload config.json demo-documents --key config/settings.json
echo ""

echo -e "${BLUE}📋 Step 6: Create Directory Structure for Sync Test${NC}"
mkdir -p demo-sync-folder/photos/2023
mkdir -p demo-sync-folder/photos/2024
mkdir -p demo-sync-folder/documents
echo "Family vacation photo 1" > demo-sync-folder/photos/2023/vacation1.jpg
echo "Family vacation photo 2" > demo-sync-folder/photos/2023/vacation2.jpg
echo "Work conference photo" > demo-sync-folder/photos/2024/conference.jpg
echo "Meeting notes document" > demo-sync-folder/documents/meeting-notes.txt
echo "Project proposal" > demo-sync-folder/documents/proposal.doc
echo -e "${GREEN}✅ Created directory structure${NC}"
echo ""

echo -e "${BLUE}📋 Step 7: Sync Entire Directory${NC}"
python object_storage_client.py sync demo-sync-folder demo-photos --prefix "synced/"
echo ""

echo -e "${BLUE}📋 Step 8: List Objects in Buckets${NC}"
echo -e "${YELLOW}Photos bucket:${NC}"
python object_storage_client.py list-objects demo-photos
echo ""
echo -e "${YELLOW}Documents bucket:${NC}"
python object_storage_client.py list-objects demo-documents
echo ""

echo -e "${BLUE}📋 Step 9: Download Files${NC}"
mkdir -p downloads
python object_storage_client.py download demo-photos photos/vacation.txt --output downloads/vacation.txt
python object_storage_client.py download demo-documents documents/report.pdf --output downloads/report.pdf
echo -e "${GREEN}✅ Downloaded files to downloads/ folder${NC}"
echo ""

echo -e "${BLUE}📋 Step 10: Verify Downloaded Content${NC}"
echo -e "${YELLOW}vacation.txt content:${NC}"
cat downloads/vacation.txt
echo ""
echo -e "${YELLOW}report.pdf content:${NC}"
cat downloads/report.pdf
echo ""

echo -e "${GREEN}🎉 Demo Complete!${NC}"
echo ""
echo -e "${YELLOW}Summary of Features Demonstrated:${NC}"
echo "✅ Health monitoring"
echo "✅ Bucket creation and management"
echo "✅ Individual file upload/download"
echo "✅ Directory synchronization"
echo "✅ Multi-protocol support (S3, WebDAV)"
echo "✅ iOS/macOS integration ready"
echo "✅ File deduplication"
echo "✅ Secure HTTPS with self-signed certificates"
echo ""
echo -e "${BLUE}🔗 Full documentation: docs/object-storage.md${NC}"

# Cleanup demo files
echo ""
echo -e "${YELLOW}Cleaning up demo files...${NC}"
rm -f demo-photo.txt demo-doc.pdf config.json
rm -rf demo-sync-folder downloads
echo -e "${GREEN}✅ Cleanup complete${NC}"