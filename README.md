# Engineering Tools

A collection of utility tools for various engineering tasks.

## Tools Available

### LDAP Server & Admin Tools
A lightweight, Python-based LDAP server with administrative utilities for user and group management.

- **[LDAP Server](docs/ldap-server.md)** - Standalone LDAP server with JSON-based data persistence
- **[LDAP Admin](docs/ldap-admin.md)** - Command-line tool for managing LDAP users and groups

### Object Storage Server & Client
A high-performance, multi-protocol object storage server with comprehensive client tools for file management.

- **[Object Storage System](docs/object-storage.md)** - Multi-protocol storage server (S3, Azure, GCS, WebDAV) with mobile device support

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/ooRickoo/engineeringtools.git
   cd engineeringtools
   ```

2. Set up a Python virtual environment:
   ```bash
   python -m venv .tools
   source .tools/bin/activate  # On macOS/Linux
   # or
   .tools\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Navigate to the specific tool directory and follow its documentation.

## Contributing

Feel free to contribute additional engineering tools or improvements to existing ones. Please ensure all tools include proper documentation and follow the established patterns.

## License

This project is open source. Please see individual tool directories for specific licensing information.
