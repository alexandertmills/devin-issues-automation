# GitHub App Authentication Workflow

This document details the complete authentication workflow for fetching GitHub issues using GitHub App authentication in the devin-issues-automation system.

## Overview

The system uses GitHub App authentication to securely access GitHub repositories and fetch issues. This involves a multi-step authentication process that generates short-lived tokens for API access.

## Prerequisites

Before the workflow can begin, the following setup must be completed:

1. **GitHub App Creation**: A GitHub App must be created in GitHub's developer settings
2. **App Installation**: Users must install the GitHub App on their account/organization and select which repositories to grant access to
3. **Credentials Configuration**: The following secrets must be configured:
   - `GITHUB_APP_ID`: The numeric ID of your GitHub App
   - `GITHUB_APP_PRIVATE_KEY`: The private key generated for your GitHub App
   - `GITHUB_APP_INSTALLATION_ID`: The installation ID for the specific user/organization

## Complete Authentication Workflow

### Step 1: User Initiates Issue Fetch

**Frontend Action**: User clicks "Fetch Issues" button in the React dashboard

**API Call**: Frontend makes GET request to backend endpoint:
```
GET /issues/{owner}/{repo}
```

**Code Reference**: `backend/app/main.py` line 104

### Step 2: Backend Initializes GitHub Client

**Backend Action**: FastAPI endpoint creates `GitHubClient` instance

**Authentication Setup**: Client checks for GitHub App credentials and calls `_setup_app_authentication()`

**Code Reference**: `backend/app/github_client.py` lines 21-22

### Step 3: JWT Token Generation

**Purpose**: Create a JSON Web Token to authenticate with GitHub as the GitHub App

**Process**:
- Generate current timestamp
- Create JWT payload with:
  - `iat` (issued at): Current timestamp
  - `exp` (expires): Current timestamp + 600 seconds (10 minutes)
  - `iss` (issuer): GitHub App ID

**Signing**: JWT is signed using the GitHub App's private key with RS256 algorithm

**Important Dependency**: The `cryptography` package is required for RS256 algorithm support. This is a common recurring issue - if you encounter "Algorithm 'RS256' could not be found" errors, ensure `cryptography` is listed in `backend/pyproject.toml` dependencies.

**Code Reference**: `backend/app/github_client.py` lines 42-51

```python
def _generate_jwt(self) -> str:
    now = int(time.time())
    payload = {
        'iat': now,
        'exp': now + 600,  # 10 minutes
        'iss': self.app_id
    }
    return jwt.encode(payload, self.private_key, algorithm='RS256')
```

### Step 4: Installation Token Request

**Purpose**: Exchange the JWT for an installation access token

**API Call**: POST request to GitHub's installation token endpoint:
```
POST https://api.github.com/app/installations/{installation_id}/access_tokens
```

**Headers**:
- `Authorization: Bearer {jwt_token}`
- `Accept: application/vnd.github.v3+json`

**Installation ID Role**: The `installation_id` identifies which specific installation of your GitHub App to authenticate with. This is crucial because:
- GitHub Apps can be installed on multiple user/organization accounts
- Each installation has its own permissions and repository access
- The installation ID scopes the authentication to the correct account

**Response**: GitHub returns an installation access token (expires in 1 hour)

**Code Reference**: `backend/app/github_client.py` lines 53-67

### Step 5: GitHub Issues API Call

**Purpose**: Fetch issues from the specified repository using the installation token

**API Call**: GET request to GitHub's issues endpoint:
```
GET https://api.github.com/repos/{owner}/{repo}/issues
```

**Headers**:
- `Authorization: token {installation_token}` ← **Note**: Uses installation token, NOT JWT
- `Accept: application/vnd.github.v3+json`

**Query Parameters**:
- `state`: "open" (default), "closed", or "all"
- `per_page`: 100 (fetch up to 100 issues per request)

**Code Reference**: `backend/app/github_client.py` lines 69-80

### Step 6: Data Processing and Storage

**Backend Processing**:
1. Receive issues data from GitHub API
2. Transform and store issues in PostgreSQL database
3. Return processed data to frontend

**Code Reference**: `backend/app/main.py` lines 128-154

## Token Lifecycle Management

### JWT Token
- **Lifespan**: 10 minutes
- **Purpose**: Only used to obtain installation tokens
- **Security**: Never sent to GitHub Issues API

### Installation Token
- **Lifespan**: 1 hour
- **Purpose**: Used for all GitHub API calls
- **Refresh**: Must be regenerated before expiration

### Current Implementation Limitations

⚠️ **Production Concern**: The current implementation has a critical limitation:

- Installation tokens are only fetched once during `GitHubClient` initialization
- No token refresh logic exists
- Long-running services will fail after 1 hour when tokens expire

### Recommended Improvements

For production use, implement:

1. **Token Caching**: Store installation tokens with expiration timestamps
2. **Automatic Refresh**: Refresh tokens before they expire
3. **Error Handling**: Handle 401 errors by refreshing tokens
4. **Token Reuse**: Reuse valid tokens across multiple API calls

## Security Considerations

1. **Private Key Protection**: GitHub App private key must be securely stored
2. **Token Scope**: Installation tokens are scoped to specific repositories
3. **Token Expiration**: Short-lived tokens minimize security risk
4. **No Persistent Storage**: Tokens should not be stored long-term

## Error Scenarios

### Common Failure Points

1. **Invalid Installation ID**: Results in 404 when requesting installation token
2. **Expired JWT**: Results in 401 when requesting installation token
3. **Expired Installation Token**: Results in 401 when calling GitHub API
4. **Insufficient Permissions**: Results in 403 when accessing repositories

### Error Handling

The current implementation includes basic error handling:
- Try/catch blocks around API calls
- Error logging for debugging
- Graceful fallback to empty results

## API Endpoints Summary

| Step | Method | Endpoint | Purpose | Auth Header |
|------|--------|----------|---------|-------------|
| 4 | POST | `/app/installations/{id}/access_tokens` | Get installation token | `Bearer {jwt}` |
| 5 | GET | `/repos/{owner}/{repo}/issues` | Fetch issues | `token {installation_token}` |

## Code Files Reference

- **Main Authentication Logic**: `backend/app/github_client.py`
- **API Endpoints**: `backend/app/main.py`
- **Database Models**: `backend/app/models.py`
- **Environment Configuration**: `backend/.env`

## Conclusion

The GitHub App authentication workflow provides secure, scoped access to GitHub repositories through a multi-step token exchange process. While the current implementation works for basic use cases, production deployments should implement proper token lifecycle management to handle long-running services and token expiration scenarios.
