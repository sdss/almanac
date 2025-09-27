# ReadTheDocs Setup Guide

This guide helps you set up ReadTheDocs.org integration for the almanac project.

## ReadTheDocs.org Setup

### 1. Create ReadTheDocs Account

1. Go to [ReadTheDocs.org](https://readthedocs.org/)
2. Sign up with your GitHub account
3. Import your `almanac` repository

### 2. Configure Project Settings

In your ReadTheDocs project settings:

#### Basic Settings
- **Name**: `almanac` or `sdss-almanac`
- **Repository URL**: `https://github.com/sdss/almanac`
- **Default Branch**: `main` (or `master`)

#### Advanced Settings
- **Python Interpreter**: CPython 3.11
- **Requirements File**: `docs/requirements.txt`
- **Use system packages**: ❌ (unchecked)
- **Privacy Level**: Public

### 3. Webhook Configuration (Optional)

For automatic builds on GitHub pushes:

1. In ReadTheDocs project settings, go to **Integrations**
2. Copy the webhook URL
3. In GitHub repository settings:
   - Go to **Settings** → **Webhooks**
   - Add webhook with the ReadTheDocs URL
   - Set **Content type** to `application/json`
   - Select **Just the push event**

Alternatively, add the webhook URL as a GitHub secret:
1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Add secret `READTHEDOCS_WEBHOOK_URL` with the webhook URL

### 4. Build Configuration

The project uses `.readthedocs.yaml` for configuration:

```yaml
version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
sphinx:
  configuration: docs/conf.py
formats:
  - pdf
  - epub
python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - docs
    - requirements: docs/requirements.txt
```

## Local Documentation Building

### Prerequisites

Install documentation dependencies:

```bash
# Install the package with docs extras
pip install -e ".[docs]"

# Or install requirements directly
pip install -r docs/requirements.txt
```

### Building Documentation

```bash
# Change to docs directory
cd docs

# Build HTML documentation
make html

# Build and serve locally
make serve  # Serves at http://localhost:8000

# Live rebuilding (requires sphinx-autobuild)
pip install sphinx-autobuild
make livehtml
```

### Available Make Targets

```bash
make html        # Build HTML documentation
make clean       # Clean build directory
make linkcheck   # Check for broken links
make serve       # Build and serve locally
make livehtml    # Live rebuilding with auto-refresh
```

## GitHub Actions Integration

The `.github/workflows/docs.yml` file provides:

- **Automatic building** on pushes to main/master
- **Pull request validation** for documentation changes
- **GitHub Pages deployment** (optional)
- **ReadTheDocs webhook triggering**
- **Documentation quality checks**

### Required Secrets (Optional)

Add these to GitHub repository secrets if needed:

- `READTHEDOCS_WEBHOOK_URL`: For triggering ReadTheDocs builds

## Troubleshooting

### Common Build Issues

1. **Import Errors**: Some dependencies (like `sdssdb`) may not be available during build
   - Solution: These are mocked in `conf.py` using `autodoc_mock_imports`

2. **Missing Dependencies**: Build fails due to missing packages
   - Solution: Add missing packages to `docs/requirements.txt`

3. **Sphinx Warnings**: Warnings treated as errors
   - Solution: Set `fail_on_warning: false` in `.readthedocs.yaml`

### Local Build Issues

1. **Module Not Found**: Cannot import almanac
   - Solution: Install in development mode: `pip install -e .`

2. **Missing Sphinx Extensions**: Extensions not found
   - Solution: Install docs requirements: `pip install -r docs/requirements.txt`

### ReadTheDocs Build Logs

Check build logs in ReadTheDocs dashboard:
1. Go to your project dashboard
2. Click **Builds** tab
3. Click on a specific build to see detailed logs

## Documentation Structure

The documentation includes:

- **User Documentation**: Installation, user guide, CLI reference
- **API Documentation**: Automated from docstrings using Sphinx autodoc
- **Developer Documentation**: Development setup and contributing
- **Examples**: Practical usage examples

## Updating Documentation

1. **Edit markdown files** in `docs/` directory
2. **Update API docs** by modifying docstrings in source code
3. **Commit and push** to trigger automatic rebuilds
4. **Check ReadTheDocs** for successful builds

## Custom Domain (Optional)

To use a custom domain like `docs.almanac-sdss.org`:

1. In ReadTheDocs project settings, go to **Domains**
2. Add your custom domain
3. Configure DNS CNAME record pointing to `readthedocs.io`
4. Update `pyproject.toml` Documentation URL