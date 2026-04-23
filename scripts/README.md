# TridentWear Scripts Documentation

This folder contains utility scripts for development, maintenance, and deployment of TridentWear. Each subfolder has a specific purpose.

## Quick Commands

```bash
# Validate CSS
npm run validate:css

# Sync headers across all HTML pages
npm run sync:headers

# Check if headers are synchronized
npm run check:headers

# Deploy to Railway
npm run deploy
```

---

## Folder Structure

### `/maintenance/`
Scripts for maintaining consistency across HTML pages (header sync, icon fixes, dropdown fixes).

| Script | Purpose | Usage |
|--------|---------|-------|
| `sync_headers.py` | Syncs header from index.html to all other HTML files | `python scripts/maintenance/sync_headers.py` |
| `check_headers.py` | Checks if headers in index.html match other pages | `python scripts/maintenance/check_headers.py` |
| `remove_dropdown.py` | Removes dropdown wrapper from Products nav | `python scripts/maintenance/remove_dropdown.py` |
| `replace_icon.py` | Replaces Font Awesome icon classes | `python scripts/maintenance/replace_icon.py` |
| `clean_index_icon.py` | Removes jelly-fill class from user icon | `python scripts/maintenance/clean_index_icon.py` |

**Note**: These scripts exist due to the lack of a templating system. In future, consider migrating to a static site generator (11ty, Hugo) or templating engine (EJS, Nunjucks) to eliminate the need for these maintenance scripts.

---

### `/generators/`
One-time code generators used during development. These have already completed their tasks and are archived here for reference.

| Script | Purpose | Status |
|--------|---------|--------|
| `generate_pages.py` | Generated verify.html and profile-setup.html | ✓ Completed |
| `generate_profile.js` | Generated profile.html layout | ✓ Completed |
| `generate_profile_responsive.js` | Generated responsive profile.html | ✓ Completed |
| `generate_profile_setup.py` | Generated profile-setup.html | ✓ Completed |

**Note**: These scripts are archived for reference only. The pages they generated are now part of the main site.

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
4. See `/DEPLOYMENT.md` for detailed instructions

---

## Related Utilities

### Active Frontend Utilities
- `js/utilities/auth-gate.js` - Creates login modals for protected actions (cart, wishlist, checkout)

These are integrated into the main JS modules and should not be moved.

---

## Future Improvements

1. **Eliminate maintenance scripts**: Migrate HTML to a templating system
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
