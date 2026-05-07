# TridentWear Scripts Documentation

This folder contains utility scripts for development, maintenance, and deployment of TridentWear. Each subfolder has a specific purpose.

## Quick Commands

```bash
# Validate CSS
npm run validate:css

# Deploy to Railway
npm run deploy
```

---

## Folder Structure

### `/generators/`
One-time code generators used during development. Keep active generators here only while they are still useful.

| Script | Purpose | Status |
|--------|---------|--------|
| `generate_pages.py` | Generated verify.html and profile-setup.html | ✓ Completed |
| `generate_profile_setup.py` | Generated profile-setup.html | ✓ Completed |

**Note**: Completed one-off scripts can be moved to an archive or removed after confirming they are no longer needed.

---

### `/validators/`
Scripts for validating code quality and consistency.

| Script | Purpose | Usage |
|--------|---------|-------|
| `validate-css.js` | Validates CSS syntax across all CSS files | `npm run validate:css` |

**To add**: HTML validators, JSON validators, or linting rules.

---

### `/deployment/`
Scripts for deploying to production on Railway.

| Script | Purpose | Usage |
|--------|---------|-------|
| `config_production.py` | Generates secure JWT and session secrets | `python scripts/deployment/config_production.py` |
| `deploy.sh` | Deployment setup for Linux/Mac | `bash scripts/deployment/deploy.sh` |
| `deploy.bat` | Deployment setup for Windows | `scripts/deployment/deploy.bat` |

**Steps to deploy:**
1. Run config_production.py to generate secrets
2. Add secrets to Railway environment variables
3. Run deploy script or push to Railway git remote
4. See the project README or deployment notes for detailed instructions

---

## Related Utilities

### Active Frontend Utilities
- `js/utilities/auth-gate.js` - Creates login modals for protected actions (cart, wishlist, checkout)

These are integrated into the main JS modules and should not be moved.

---

## Future Improvements

1. **Use a templating/build system**: Reduce duplicated HTML by moving shared layout into templates or components
2. **Add automated testing**: Add test scripts to validate functionality
3. **Add build process**: Add minification, bundling, asset optimization
4. **Add linting**: Add HTML, CSS, JS linters to CI/CD pipeline
5. **Add pre-commit hooks**: Validate code before allowing commits

---

## Contributing

When creating new scripts:
1. Place in appropriate folder (maintenance/generators/validators/deployment)
2. Add description to this README
3. Include docstring/comments in the script
4. Update npm scripts in package.json if it's a commonly-used utility
