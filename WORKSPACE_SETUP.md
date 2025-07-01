# Workspace Setup Guide for GitHub Issues Automation

This document provides step-by-step instructions for setting up the development environment for the GitHub Issues Automation project in a new Devin session.

## Prerequisites

### Required Secrets/Environment Variables
Ensure you have access to these secrets (they should be available as environment variables):
- `DEVIN_SERVICE_API_KEY` - Devin API key for AI integration
- `GITHUB_APP_KEY` - GitHub App private key (RSA format)
- `GITHUB_SWIFT_KEY` - GitHub personal access token for testing
- `NEON_CREDENTIALS_USER` - Neon database username
- `NEON_CREDENTIALS_PASSWROD` - Neon database password (note: typo in variable name)

### GitHub App Information
- **App ID**: 1488267
- **Client ID**: Iv23lib8BomyXulniEOX
- **Installation ID**: Not yet configured (needs to be obtained)

## Repository Setup

### 1. Git Pull - Update Repository
```bash
cd ~/repos/devin-issues-automation && git pull && git submodule update --init --recursive
```

**Note**: If this is your first time setting up, clone the repository first:
```bash
cd ~
mkdir -p repos
cd repos
git clone https://github.com/alexandertmills/devin-issues-automation.git
```

Then navigate to the repository:
```bash
cd ~/repos/devin-issues-automation
```

### 2. Check Out Working Branch
```bash
git checkout devin/1751322601-github-issues-integration
```

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd ~/repos/devin-issues-automation/backend
```

### 2. Install Dependencies
The backend uses Poetry for Python dependency management. Make sure you have Poetry installed:
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

**Key Backend Dependencies:**
- `fastapi[standard]` ^0.115.14 - Web framework with automatic OpenAPI docs
- `psycopg[binary]` ^3.2.9 - PostgreSQL adapter for Python
- `sqlalchemy` ^2.0.41 - SQL toolkit and ORM
- `asyncpg` ^0.30.0 - Async PostgreSQL driver
- `requests` ^2.32.4 - HTTP library for API calls
- `python-dotenv` ^1.1.1 - Environment variable management
- `pyjwt` ^2.10.1 - JSON Web Token implementation

### 3. Configure Environment Variables
Create/verify the `.env` file:
```bash
# The .env file should contain:
DEVIN_SERVICE_API_KEY=${DEVIN_SERVICE_API_KEY}
NEON_DATABASE_URL=postgresql://neondb_owner:npg_iw4GofnvpQ3m@ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech/neondb?sslmode=require
GITHUB_TOKEN=
GITHUB_APP_ID=1488267
GITHUB_APP_PRIVATE_KEY=${GITHUB_APP_KEY}
GITHUB_APP_INSTALLATION_ID=
GITHUB_WEBHOOK_SECRET=
```

### 4. Start Backend Development Server
```bash
poetry run fastapi dev app/main.py
```
This will start the backend on `http://localhost:8000`

### 5. Verify Backend is Working
Test the health endpoint:
```bash
curl http://localhost:8000/healthz
# Should return: {"status":"ok"}
```

## Frontend Setup

### 1. Navigate to Frontend Directory (in new terminal/shell)
```bash
cd ~/repos/devin-issues-automation/frontend
```

### 2. Install Dependencies
The frontend uses npm for Node.js dependency management:
```bash
# Install all dependencies
npm install

# Alternative: if you prefer yarn or pnpm
# yarn install
# pnpm install
```

**Key Frontend Dependencies:**
- `react` ^18.3.1 + `react-dom` ^18.3.1 - React framework
- `typescript` ~5.6.2 - TypeScript support
- `vite` ^6.0.1 - Build tool and dev server
- `tailwindcss` ^3.4.16 - Utility-first CSS framework
- `@radix-ui/*` - Comprehensive UI component library (shadcn/ui)
- `lucide-react` ^0.364.0 - Icon library
- `react-hook-form` ^7.59.0 - Form handling
- `zod` ^3.25.67 - Schema validation

**Development Dependencies:**
- `@vitejs/plugin-react` ^4.3.4 - Vite React plugin
- `eslint` ^9.15.0 + `typescript-eslint` ^8.15.0 - Linting
- `autoprefixer` ^10.4.20 + `postcss` ^8.4.49 - CSS processing

### 3. Configure Environment Variables
Create/verify the `.env` file:
```bash
# For local development:
VITE_API_URL=http://localhost:8000

# For testing with deployed backend:
VITE_API_URL=https://app-lrzjyeeg.fly.dev
```

### 4. Start Frontend Development Server
```bash
npm run dev
```
This will start the frontend on `http://localhost:5173`

**Note**: The app will be available at http://localhost:5173 (Vite default port)

## Deployed Backend Information

### Current Deployment
- **URL**: https://app-lrzjyeeg.fly.dev/
- **Status**: Working (as of last session)
- **Health Check**: https://app-lrzjyeeg.fly.dev/healthz

### Testing Deployed Backend
```bash
# Health check
curl https://app-lrzjyeeg.fly.dev/healthz

# GitHub API test
curl https://app-lrzjyeeg.fly.dev/test-github

# Devin API test (will show error - expected)
curl https://app-lrzjyeeg.fly.dev/test-devin

# GitHub App status
curl https://app-lrzjyeeg.fly.dev/github-app-status
```

## Database Information

### Neon PostgreSQL Connection
- **Host**: ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech
- **Database**: neondb
- **User**: neondb_owner
- **Password**: npg_iw4GofnvpQ3m
- **SSL Mode**: require

### Connection String
```
postgresql://neondb_owner:npg_iw4GofnvpQ3m@ep-sweet-breeze-a84hge8c-pooler.eastus2.azure.neon.tech/neondb?sslmode=require
```

## Key Files and Their Status

### Backend Files
- `app/main.py` - Main FastAPI application (✅ Working)
- `app/github_client.py` - GitHub API integration (✅ Working)
- `app/devin_client.py` - Devin API integration (⚠️ Disabled due to env vars)
- `app/models.py` - Database models (❓ Not fully tested)
- `app/database.py` - Database connection (❓ Not fully tested)
- `.env` - Environment variables (⚠️ Some missing values)

### Frontend Files
- `src/App.tsx` - Main dashboard component (✅ Working locally)
- `src/App.css` - Styling (✅ Working)
- `.env` - Environment variables (⚠️ May need backend URL update)

## Common Issues and Solutions

### Backend Won't Start
1. **Missing Dependencies**: Run `poetry install`
2. **Poetry Not Found**: Install Poetry with `curl -sSL https://install.python-poetry.org | python3 -`
3. **Python Version**: Ensure Python 3.12+ is installed (`python --version`)
4. **Environment Variables**: Check `.env` file exists and has correct format
5. **Database Connection**: Verify Neon credentials are correct
6. **Port Already in Use**: Kill existing process on port 8000 or use different port

### Frontend Won't Start
1. **Missing Dependencies**: Run `npm install`
2. **Node Version**: Ensure Node.js 18+ is installed (`node --version`)
3. **Port Conflicts**: Frontend runs on 5173, backend on 8000
4. **API Connection**: Check `VITE_API_URL` in `.env`
5. **TypeScript Errors**: Run `npm run build` to check for type errors
6. **Cache Issues**: Clear npm cache with `npm cache clean --force`

### Package Management Issues
1. **Poetry Lock File**: Delete `poetry.lock` and run `poetry install` if dependencies conflict
2. **npm Lock File**: Delete `package-lock.json` and `node_modules`, then run `npm install`
3. **Version Conflicts**: Check for peer dependency warnings and resolve manually
4. **Global vs Local**: Ensure you're using project-local versions of tools

### Deployment Issues
1. **Environment Variables**: Fly.io deployment may need env vars configured separately
2. **Dependencies**: Ensure `pyproject.toml` has all required packages
3. **CORS**: Backend has CORS configured for frontend integration

## Testing Checklist

### Before Starting Development
- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] GitHub API test endpoint works
- [ ] Database connection established (if needed)

### During Development
- [ ] Changes reflected in local servers (auto-reload enabled)
- [ ] No console errors in browser
- [ ] API endpoints return expected responses
- [ ] Database operations work correctly (if using)

### Before Deployment
- [ ] All tests pass locally
- [ ] Environment variables configured correctly
- [ ] Dependencies listed in package files
- [ ] CORS settings allow frontend access

## Setup Lint

### Backend Linting
The backend uses Python's built-in linting capabilities:
```bash
cd ~/repos/devin-issues-automation/backend

# Check code style and potential issues
poetry run python -m py_compile app/*.py

# Alternative: use flake8 if available
poetry run flake8 app/ || echo "flake8 not installed - using basic syntax check"

# Check imports and basic syntax
poetry run python -c "import app.main; print('✅ Backend imports successfully')"
```

### Frontend Linting
The frontend uses ESLint for code quality:
```bash
cd ~/repos/devin-issues-automation/frontend

# Run linter
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Check TypeScript compilation
npm run build
```

## Setup Tests

### Backend Tests
Currently, the backend uses manual testing via API endpoints:
```bash
cd ~/repos/devin-issues-automation/backend

# Start the server
poetry run fastapi dev app/main.py

# In another terminal, test endpoints:
curl http://localhost:8000/healthz
curl http://localhost:8000/test-github
curl http://localhost:8000/github-app-status
```

### Frontend Tests
The frontend uses Vite's built-in testing capabilities:
```bash
cd ~/repos/devin-issues-automation/frontend

# Type checking
npm run build

# Manual testing via browser
npm run dev
# Then open http://localhost:5173 in browser
```

**Note**: Comprehensive unit tests are not yet implemented but can be added using pytest (backend) and vitest (frontend).

## Useful Commands

### Backend Development
```bash
# Start development server with auto-reload
poetry run fastapi dev app/main.py

# Alternative: production mode
poetry run fastapi run app/main.py

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree

# Check project configuration and dependencies
poetry check

# Show outdated packages
poetry show --outdated

# Database operations (if needed)
poetry run python -c "from app.database import create_tables; create_tables()"

# Run Python shell with project dependencies
poetry shell
```

### Frontend Development
```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run linter
npm run lint

# Add new dependency
npm install package-name

# Add development dependency
npm install --save-dev package-name

# Update dependencies
npm update

# Check for security vulnerabilities
npm audit

# Fix security vulnerabilities automatically
npm audit fix

# Clean install (removes node_modules and reinstalls)
rm -rf node_modules package-lock.json && npm install
```

### Deployment
```bash
# Deploy backend (from backend directory)
# Use Devin's deploy_backend command

# Deploy frontend (from frontend directory)
# Use Devin's deploy_frontend command with dist/ directory
```

## Dependency Status (Last Updated: June 30, 2025)

### Backend Dependencies
- **Status**: ✅ Up to date
- **Last Update**: Dependencies checked and updated via `poetry update`
- **Security**: ✅ No vulnerabilities found via `poetry check`
- **Known Outdated**: 2 minor packages (pydantic-core, starlette) - constrained by compatibility

### Frontend Dependencies
- **Status**: ✅ Recently updated
- **Last Update**: 5 packages updated via `npm update`
- **Security**: ✅ 0 vulnerabilities found via `npm audit`
- **Major Updates Available**: React 19, Vite 7.0, Tailwind CSS 4.1 (not applied due to breaking changes)

### Dependency Update Commands
```bash
# Backend - check and update
cd ~/repos/devin-issues-automation/backend
poetry show --outdated
poetry update
poetry check

# Frontend - check and update
cd ~/repos/devin-issues-automation/frontend
npm outdated
npm update
npm audit

# Alternative: maintain dependencies during session startup
cd ~/repos/devin-issues-automation/frontend && npm install
```

## Next Session Priorities

1. **Fix Known Issues**:
   - test-devin endpoint bug
   - Frontend backend URL configuration
   - GitHub App Installation ID

2. **Complete Testing**:
   - End-to-end issue fetching
   - Database operations
   - Error handling

3. **Integration Work**:
   - Frontend-backend communication
   - GitHub webhook processing
   - Multi-repository support

4. **Documentation**:
   - API documentation
   - User guide
   - Deployment guide

## Additional Notes

### Development Workflow
1. **Always start with git pull** to get latest changes
2. **Install/update dependencies** after pulling changes
3. **Run linting** before committing changes
4. **Test locally** before deploying
5. **Check both backend and frontend** are working together

### Advanced Setup Tips (from Devin Documentation)
- **Use ~/.bashrc for environment setup**: Edit `~/.bashrc` to automatically configure environments
- **Use direnv for environment variables**: Install `direnv` and create `.envrc` files for repo-specific variables
- **Add directories to PATH**: Export custom paths in `~/.bashrc` for easier executable access
- **Configure different environments per repo**: Use custom cd functions to automatically switch Node/Python versions
- **Set up gitignore**: Prevent Devin from committing unwanted files

### Environment Considerations
- Backend runs on port 8000
- Frontend runs on port 5173 (not 3000 as some examples show)
- Database is hosted on Neon (cloud PostgreSQL)
- Deployed backend is on Fly.io

### Troubleshooting Quick Reference
- **Backend won't start**: Check Poetry installation and .env file
- **Frontend won't start**: Check Node.js version and npm install
- **API calls failing**: Verify backend is running and CORS is configured
- **Database issues**: Check Neon credentials and connection string
- **Commands not verifying**: Check absolute paths, install dependencies, verify directory context
- **Commands work manually but not in setup**: Edit `~/.bashrc` to ensure fresh shells have access to tools
- **Git pull failing**: Verify Devin has access to repository and submodules
- **Homebrew asking for password**: Use `CI=1 brew install <package>` instead

## Project Structure Reference
```
~/repos/devin-issues-automation/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # Database models
│   │   ├── database.py       # DB connection
│   │   ├── github_client.py  # GitHub API
│   │   └── devin_client.py   # Devin API
│   ├── .env                  # Environment variables
│   └── pyproject.toml        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   └── App.css          # Styling
│   ├── .env                 # Environment variables
│   └── package.json         # Node dependencies
├── PROJECT_STATUS.md        # This session's status
└── WORKSPACE_SETUP.md       # This setup guide
```

This setup guide should get you up and running quickly in a new session. Remember to check the PROJECT_STATUS.md file for current status and known issues before starting development.
