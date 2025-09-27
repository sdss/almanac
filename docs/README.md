# almanac Documentation

This directory contains comprehensive documentation for the `almanac` project.

## Documentation Structure

- **[Installation Guide](installation.md)** - Complete installation instructions for all environments
- **[User Guide](user-guide.md)** - Comprehensive user guide and tutorials
- **[API Reference](api-reference.md)** - Complete API documentation for all modules
- **[Configuration Guide](configuration.md)** - Configuration options and settings
- **[Data Formats](data-formats.md)** - HDF5 output formats and data structures
- **[Development Guide](development.md)** - Development setup, contributing guidelines, and testing
- **[CLI Reference](cli-reference.md)** - Complete command-line interface documentation
- **[Examples](examples/)** - Usage examples and tutorials
- **[FAQ](faq.md)** - Frequently asked questions and troubleshooting

## Quick Links

- [Getting Started](../README.md#getting-started)
- [Project Repository](https://github.com/sdss/almanac)
- [Issue Tracker](https://github.com/sdss/almanac/issues)

## Building Documentation

### Online Documentation

The documentation is automatically built and hosted on **ReadTheDocs.org**:
- **Latest Docs**: https://sdss-almanac.readthedocs.io/
- **PDF Version**: Available on ReadTheDocs
- **ePub Version**: Available on ReadTheDocs

### Local Building

Documentation can be built locally using Sphinx:

```bash
# Install documentation dependencies
pip install -e ".[docs]"
pip install -r docs/requirements.txt

# Build HTML documentation
cd docs
make html

# Build and serve locally at http://localhost:8000
make serve

# Live rebuilding with auto-refresh
make livehtml
```

### ReadTheDocs Integration

The project uses:
- **`.readthedocs.yaml`**: Configuration for ReadTheDocs.org builds
- **GitHub Actions**: Automated documentation building and deployment
- **Sphinx**: Documentation generation from both Markdown and RST sources

See [`setup_rtd.md`](setup_rtd.md) for complete ReadTheDocs setup instructions.