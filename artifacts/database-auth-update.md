# Database Schema Update: External Authentication
## Contract Refund Eligibility System

**Date:** 2025-11-06
**Status:** ✅ Complete
**Change Type:** Architecture Update

---

## Summary

Updated database schema to use external authentication provider instead of storing passwords locally. This is a more secure and scalable approach for production systems.

---

## Changes Made

### 1. Users Table Schema

**Before:**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- REMOVED
    role VARCHAR(20) NOT NULL,
    ...
);
```

**After:**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,

    -- External auth provider identifiers
    auth_provider VARCHAR(50) NOT NULL,              -- NEW
    auth_provider_user_id VARCHAR(255) UNIQUE NOT NULL,  -- NEW (sub claim from JWT)

    -- User profile data (from auth provider)
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100),  -- Now nullable
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- Application-specific authorization
    role VARCHAR(20) NOT NULL,
    ...
);
```

**Key Changes:**
- ❌ Removed `password_hash` column
- ✅ Added `auth_provider` (e.g., 'auth0', 'okta', 'cognito')
- ✅ Added `auth_provider_user_id` (unique ID from auth provider, maps to JWT `sub` claim)
- ✅ Made `username` nullable (may not be provided by all auth providers)
- ✅ Added index on `auth_provider_user_id`

### 2. Sessions Table Schema

**Before:**
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    jwt_token TEXT NOT NULL,        -- REMOVED
    refresh_token UUID,              -- REMOVED
    ip_address INET,
    user_agent TEXT,
    ...
);
```

**After:**
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,

    -- Session metadata only (no tokens)
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN,
);
```

**Key Changes:**
- ❌ Removed `jwt_token` field (managed by external auth provider)
- ❌ Removed `refresh_token` field (managed by external auth provider)
- ✅ Sessions now only track metadata for audit purposes

### 3. Seed Data Updates

**Before:**
```sql
INSERT INTO users (username, email, password_hash, role, ...) VALUES
    ('admin', 'admin@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ckQZBdP.yVnC', 'admin', ...);
```

**After:**
```sql
INSERT INTO users (auth_provider, auth_provider_user_id, email, username, role, ...) VALUES
    ('auth0', 'auth0|admin-mock-sub-123456', 'admin@company.com', 'admin', 'admin', ...);
```

**Key Changes:**
- ❌ No password hashes
- ✅ Mock auth provider IDs for development/testing
- ✅ Updated success message to reflect external auth

### 4. Documentation Updates

**Files Updated:**
- ✅ `schema.sql` - Updated DDL and comments
- ✅ `seed_data.sql` - Removed passwords, added auth provider IDs
- ✅ `data-dictionary.md` - Updated users and sessions table documentation
- ✅ `README.md` - Updated authentication section

---

## Authentication Flow

### How It Works

1. **User Login:**
   ```
   User → External Auth Provider (Auth0/Okta/Cognito) → JWT Token
   ```

2. **First Login (User Creation):**
   ```
   1. User authenticates with external provider
   2. Backend receives JWT with user info
   3. Backend extracts `sub` claim (unique user ID)
   4. Backend creates user record in database:
      - auth_provider: 'auth0'
      - auth_provider_user_id: 'auth0|507f1f77bcf86cd799439011'
      - email, first_name, last_name: from JWT claims
      - role: assigned by application logic (default 'user')
   ```

3. **Subsequent Requests:**
   ```
   1. Frontend sends JWT in Authorization header
   2. Backend validates JWT with auth provider
   3. Backend extracts `sub` claim
   4. Backend looks up user by auth_provider_user_id
   5. Backend checks user.role for authorization
   ```

4. **Session Tracking (Optional):**
   ```
   - Session record created for audit trail
   - Stores IP address, user agent, timestamps
   - Does NOT store JWT (managed by auth provider)
   ```

---

## Benefits

### 1. Security
- ✅ **No password storage** - Eliminates password breach risk
- ✅ **Reduced attack surface** - No password reset flows, no credential stuffing
- ✅ **MFA support** - Handled by auth provider
- ✅ **Better secret management** - Auth provider handles token encryption

### 2. Compliance
- ✅ **Easier audits** - Auth provider handles authentication compliance
- ✅ **GDPR compliance** - Right to be forgotten handled by auth provider
- ✅ **SOC 2 compliance** - Auth provider typically SOC 2 certified

### 3. User Experience
- ✅ **Single Sign-On (SSO)** - Users can use existing credentials
- ✅ **Social login** - Google, Microsoft, GitHub, etc.
- ✅ **Passwordless** - Magic links, biometrics, etc.

### 4. Development
- ✅ **Less code** - No password hashing, reset flows, email verification
- ✅ **Faster development** - Auth provider handles complex auth logic
- ✅ **Better testing** - Mock auth provider for tests

---

## Integration Requirements

### Backend (FastAPI)

**JWT Validation Middleware:**
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials

    # Validate JWT with auth provider (e.g., Auth0)
    try:
        # Decode and verify JWT signature
        payload = jwt.decode(
            token,
            auth_provider_public_key,
            algorithms=["RS256"],
            audience=AUTH_AUDIENCE,
            issuer=AUTH_ISSUER
        )

        # Extract user info
        sub = payload.get("sub")  # auth_provider_user_id
        email = payload.get("email")

        # Look up or create user in database
        user = get_or_create_user(
            auth_provider="auth0",
            auth_provider_user_id=sub,
            email=email
        )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**User Lookup/Creation:**
```python
def get_or_create_user(auth_provider: str, auth_provider_user_id: str, email: str):
    # Look up user by auth_provider_user_id
    user = db.query(User).filter(
        User.auth_provider_user_id == auth_provider_user_id
    ).first()

    if not user:
        # Create new user on first login
        user = User(
            auth_provider=auth_provider,
            auth_provider_user_id=auth_provider_user_id,
            email=email,
            role="user",  # Default role
            is_active=True
        )
        db.add(user)
        db.commit()

    return user
```

### Frontend (Next.js)

**Auth Provider SDK:**
```typescript
// Using Auth0 as example
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

// App wrapper
<Auth0Provider
  domain={process.env.NEXT_PUBLIC_AUTH0_DOMAIN}
  clientId={process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID}
  authorizationParams={{
    redirect_uri: window.location.origin,
    audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
  }}
>
  <App />
</Auth0Provider>

// Login component
const { loginWithRedirect, user, getAccessTokenSilently } = useAuth0();

// Get token for API calls
const token = await getAccessTokenSilently();
axios.get('/api/contracts', {
  headers: { Authorization: `Bearer ${token}` }
});
```

---

## Auth Provider Configuration

### Supported Providers

1. **Auth0**
   - Full-featured, easy to integrate
   - Good free tier
   - Recommended for MVP

2. **AWS Cognito**
   - Good if already using AWS
   - Lower cost for high volume
   - More complex setup

3. **Okta**
   - Enterprise-focused
   - Strong compliance features
   - Higher cost

4. **Supabase Auth**
   - Open source option
   - Good for startups
   - Self-hostable

### Configuration Steps (Auth0 Example)

1. **Create Auth0 Application:**
   - Type: Single Page Application
   - Allowed Callback URLs: `http://localhost:3000, https://yourapp.com`
   - Allowed Logout URLs: `http://localhost:3000, https://yourapp.com`

2. **Configure JWT:**
   - Add custom claims for role (if needed)
   - Set token expiration (4 hours recommended)

3. **Environment Variables:**
   ```env
   # Frontend
   NEXT_PUBLIC_AUTH0_DOMAIN=your-tenant.auth0.com
   NEXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id
   NEXT_PUBLIC_AUTH0_AUDIENCE=https://your-api.com

   # Backend
   AUTH0_DOMAIN=your-tenant.auth0.com
   AUTH0_AUDIENCE=https://your-api.com
   AUTH0_ISSUER=https://your-tenant.auth0.com/
   ```

---

## Migration Strategy

### For Existing Users (If Applicable)

If migrating from password-based auth:

1. **Add Migration Window:**
   - Email users about auth provider change
   - Provide 30-day migration window

2. **One-Time Migration:**
   ```sql
   -- Create users in auth provider via API
   -- Update database with auth_provider_user_id
   UPDATE users
   SET auth_provider = 'auth0',
       auth_provider_user_id = 'auth0|<new-sub-from-provider>'
   WHERE email = 'user@example.com';
   ```

3. **Deprecate Password Auth:**
   - Remove password column after migration complete
   - Archive old password hashes (if needed for legal)

### For Greenfield (This Project)

- ✅ No migration needed
- ✅ Users created on first login
- ✅ Start with external auth from day 1

---

## Testing

### Unit Tests

```python
def test_get_or_create_user():
    # Test user creation on first login
    user = get_or_create_user(
        auth_provider="auth0",
        auth_provider_user_id="auth0|test123",
        email="test@example.com"
    )
    assert user.auth_provider == "auth0"
    assert user.auth_provider_user_id == "auth0|test123"
    assert user.role == "user"

    # Test user lookup on subsequent login
    user2 = get_or_create_user(
        auth_provider="auth0",
        auth_provider_user_id="auth0|test123",
        email="test@example.com"
    )
    assert user.user_id == user2.user_id
```

### Integration Tests

```python
def test_auth_flow():
    # Mock JWT token
    mock_token = create_mock_jwt(sub="auth0|test123", email="test@example.com")

    # Make authenticated request
    response = client.get(
        "/api/contracts",
        headers={"Authorization": f"Bearer {mock_token}"}
    )
    assert response.status_code == 200
```

---

## Rollback Plan

If needed to rollback:

1. **Add password_hash column back:**
   ```sql
   ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
   ```

2. **Update seed data** with password hashes

3. **Revert authentication middleware** to password-based

4. **Update frontend** to use email/password login

---

## Next Steps

1. ✅ Database schema updated
2. ⏳ Choose auth provider (recommended: Auth0 for MVP)
3. ⏳ Set up auth provider account and application
4. ⏳ Implement JWT validation middleware in backend
5. ⏳ Integrate auth provider SDK in frontend
6. ⏳ Test authentication flow end-to-end
7. ⏳ Update deployment configuration with auth provider credentials

---

## References

- [Auth0 Documentation](https://auth0.com/docs)
- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Okta Documentation](https://developer.okta.com/)
- [JWT.io](https://jwt.io/) - JWT debugger
- [OpenID Connect Specification](https://openid.net/connect/)

---

**Status: Database Schema Ready for External Auth ✅**

All database changes are complete. Backend and frontend integration with auth provider is next.

---

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Claude Code | Updated database schema for external authentication |

---

**End of Auth Update Document**
