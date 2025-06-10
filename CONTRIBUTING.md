# Contributing to Engineering Tools

Thank you for your interest in contributing to the Engineering Tools project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Issues

- Use the GitHub Issues page to report bugs or request features
- Provide clear descriptions and steps to reproduce issues
- Include relevant system information (OS, Python version, etc.)

### Contributing Code

1. **Fork the repository** and create a feature branch from `main`
2. **Make your changes** with clear, descriptive commit messages
3. **Add tests** if applicable (we encourage testing for all tools)
4. **Update documentation** for any new features or changes
5. **Submit a pull request** with a clear description of your changes

### Code Standards

- Follow PEP 8 Python style guidelines
- Include docstrings for functions and classes
- Add type hints where appropriate
- Keep functions focused and modular

### Documentation

- Update relevant `.md` files in the `docs/` directory
- Include usage examples for new features
- Update the main README.md if adding new tools

### Adding New Tools

When adding a new engineering tool:

1. **Create the tool** in the root directory with a descriptive filename
2. **Add documentation** in the `docs/` directory
3. **Update README.md** to include the new tool in the tools list
4. **Include examples** and usage instructions
5. **Add any dependencies** to `requirements.txt`

### Tool Requirements

Each tool should:

- Be self-contained and focused on a specific engineering task
- Include comprehensive documentation
- Handle errors gracefully with helpful messages
- Follow the existing code style and structure
- Include usage examples

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ooRickoo/engineeringtools.git
   cd engineeringtools
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .tools
   source .tools/bin/activate  # macOS/Linux
   # or .tools\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Questions?

Feel free to open an issue if you have questions about contributing or need clarification on any guidelines.

Thank you for helping improve Engineering Tools!
