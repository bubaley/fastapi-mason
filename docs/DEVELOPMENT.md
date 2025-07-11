# FastAPI Mason Documentation

This directory contains the documentation for FastAPI Mason using MkDocs with Material theme.

## Setup

### Using uv (Recommended)

1. Install documentation dependencies:
```bash
uv sync --group docs
```

2. Serve the documentation locally:
```bash
uv run mkdocs serve
```

3. Build the documentation:
```bash
uv run mkdocs build
```

## Automatic Deployment

Documentation is automatically built and deployed to GitHub Pages when:

- ✅ Changes are pushed to the `main` branch
- ✅ Changes affect documentation files (`docs/**`, `mkdocs.yml`, `pyproject.toml`)
- ✅ All checks pass (build validation, link checking, etc.)

### For Pull Requests

When you create a PR that affects documentation:

- 🔍 Documentation build is validated
- 🔗 Internal links are checked
- ✨ Basic markdown validation is performed
- 📝 Spell checking for common typos

The checks run via GitHub Actions and must pass before merging.

## Structure

- `index.md` - Main landing page
- `quick-start.md` - Getting started guide
- `viewsets/` - ViewSets documentation
- `schemas.md` - Schema generation guide
- `pagination.md` - Pagination strategies
- `permissions.md` - Permission system
- `state.md` - State management
- `wrappers.md` - Response wrappers

## Contributing

When adding new documentation:

1. Follow the existing structure and style
2. Use clear, descriptive headings
3. Include practical examples
4. Test code examples before committing
5. Update navigation in `mkdocs.yml` if needed 