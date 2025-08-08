# 🔒 Security Guide

This document outlines the security features, best practices, and recommendations for deploying and maintaining a secure Flokie application.

## 🛡️ Built-in Security Features

### Authentication & Authorization

#### JWT Token Security
- **Secure Token Generation**: Uses cryptographically secure random number generation
- **Token Expiration**: Configurable short-lived access tokens (default: 1 hour)
- **Refresh Token Rotation**: Long-lived refresh tokens with rotation capability
- **Token Blacklisting**: Support for token revocation and blacklisting

```python
# Token configuration
JWT_ACCESS_TOKEN_EXPIRES_HOURS=1
JWT_REFRESH_TOKEN_EXPIRES_DAYS=30
JWT_SECRET_KEY=your-cryptographically-secure-secret-key
```

#### Password Security
- **Bcrypt Hashing**: Industry-standard password hashing with salt
- **Password Strength Requirements**: Configurable complexity rules
- **Account Lockout**: Automatic lockout after failed login attempts
- **Password History**: Prevention of password reuse

```python
# Password security settings
MIN_PASSWORD_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=30  # minutes
PASSWORD_HISTORY_COUNT=5
```

### Input Validation & Sanitization

#### Request Validation
- **Schema Validation**: Comprehensive input validation using Marshmallow
- **Type Checking**: Strict type validation for all inputs
- **Length Limits**: Configurable field length restrictions
- **Format Validation**: Email, URL, and custom format validation

```python
# Example validation schema
class UserRegistrationSchema(Schema):
    username = fields.Str(required=True, validate=Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=Length(min=8))
```

#### SQL Injection Prevention
- **Parameterized Queries**: SQLAlchemy ORM prevents SQL injection
- **Input Sanitization**: Automatic input sanitization
- **Query Validation**: Validation of dynamic query parameters

### Cross-Site Scripting (XSS) Protection

#### Output Encoding
- **Automatic Escaping**: Flask's Jinja2 templates auto-escape output
- **Content Security Policy**: Configurable CSP headers
- **Input Sanitization**: HTML and script tag filtering

```python
# CSP Configuration
CONTENT_SECURITY_POLICY = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:",
}
```

### Cross-Site Request Forgery (CSRF) Protection

#### CSRF Tokens
- **Token Generation**: Automatic CSRF token generation
- **Token Validation**: Server-side token validation
- **SameSite Cookies**: Cookie security attributes

```python
# CSRF Configuration
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
SESSION_COOKIE_SAMESITE='Lax'
```

## 🔐 Security Headers

### HTTP Security Headers

Flokie automatically sets security headers:

```python
# Security headers configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

### CORS Configuration

```python
# CORS settings
CORS_ORIGINS = ['https://yourdomain.com', 'https://www.yourdomain.com']
CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
CORS_SUPPORTS_CREDENTIALS = True
```

## 🚨 Security Best Practices

### Environment Configuration

#### Secret Management
```bash
# Use strong, unique secrets
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Never commit secrets to version control
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

#### Database Security
```bash
# Use strong database passwords
DB_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Restrict database access
DATABASE_URL=postgresql://limited_user:${DB_PASSWORD}@localhost/myapp

# Enable SSL for database connections
DATABASE_URL=postgresql://user:pass@localhost/db?sslmode=require
```

### Production Deployment

#### HTTPS Configuration
```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_dhparam /path/to/dhparam.pem;
}
```

#### Container Security
```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Read-only filesystem
docker run --read-only --tmpfs /tmp myapp

# Security options
docker run --security-opt=no-new-privileges:true myapp
```

### Rate Limiting

#### API Rate Limiting
```python
# Rate limiting configuration
RATE_LIMITS = {
    'default': '100 per hour',
    'auth.login': '5 per minute',
    'auth.register': '3 per minute',
    'password.reset': '2 per minute',
}
```

#### DDoS Protection
```nginx
# Nginx rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
}

server {
    location /api/ {
        limit_req zone=api burst=20 nodelay;
    }

    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
    }
}
```

## 🔍 Security Monitoring

### Logging Security Events

```python
# Security event logging
@app.before_request
def log_security_events():
    # Log authentication attempts
    if request.endpoint in ['auth.login', 'auth.register']:
        logger.info('Authentication attempt', extra={
            'endpoint': request.endpoint,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            'timestamp': datetime.utcnow()
        })

    # Log suspicious activity
    if request.headers.get('X-Forwarded-For'):
        logger.warning('Request with X-Forwarded-For header', extra={
            'ip_address': request.remote_addr,
            'forwarded_for': request.headers.get('X-Forwarded-For')
        })
```

### Error Monitoring

```python
# Sentry configuration for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)
```

### Intrusion Detection

```python
# Failed login attempt monitoring
class SecurityMonitor:
    @staticmethod
    def track_failed_login(username, ip_address):
        # Track failed attempts
        failed_attempts = cache.get(f"failed_login:{ip_address}", 0)
        failed_attempts += 1
        cache.set(f"failed_login:{ip_address}", failed_attempts, timeout=3600)

        # Alert on suspicious activity
        if failed_attempts > 10:
            logger.critical('Potential brute force attack', extra={
                'ip_address': ip_address,
                'username': username,
                'attempts': failed_attempts
            })
```

## 🛠️ Security Testing

### Automated Security Testing

```bash
# Security scanning with bandit
bandit -r app/ -f json -o security-report.json

# Dependency vulnerability scanning
safety check --json --output security-deps.json

# Container security scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image myapp:latest
```

### Manual Security Testing

#### Authentication Testing
```python
# Test JWT token validation
def test_invalid_token():
    headers = {'Authorization': 'Bearer invalid-token'}
    response = client.get('/api/users/profile', headers=headers)
    assert response.status_code == 401

# Test password strength
def test_weak_password():
    data = {'username': 'test', 'password': '123'}
    response = client.post('/api/auth/register', json=data)
    assert response.status_code == 400
```

#### Input Validation Testing
```python
# Test SQL injection prevention
def test_sql_injection():
    malicious_input = "'; DROP TABLE users; --"
    data = {'username': malicious_input}
    response = client.post('/api/auth/register', json=data)
    assert response.status_code == 400

# Test XSS prevention
def test_xss_prevention():
    xss_payload = "<script>alert('xss')</script>"
    data = {'bio': xss_payload}
    response = client.put('/api/users/profile', json=data)
    # Verify payload is escaped in response
```

## 🚨 Incident Response

### Security Incident Checklist

1. **Immediate Response**
   - [ ] Identify the scope of the incident
   - [ ] Isolate affected systems
   - [ ] Preserve evidence
   - [ ] Notify stakeholders

2. **Investigation**
   - [ ] Analyze logs and monitoring data
   - [ ] Identify attack vectors
   - [ ] Assess data exposure
   - [ ] Document findings

3. **Containment**
   - [ ] Patch vulnerabilities
   - [ ] Update security configurations
   - [ ] Revoke compromised credentials
   - [ ] Implement additional monitoring

4. **Recovery**
   - [ ] Restore services
   - [ ] Verify system integrity
   - [ ] Update security measures
   - [ ] Conduct post-incident review

### Emergency Procedures

```bash
# Emergency user lockout
flask shell
>>> from app.models.user import User
>>> user = User.get_by_username('compromised_user')
>>> user.deactivate()
>>> user.save()

# Emergency token revocation
>>> from app.extensions import jwt
>>> jwt.revoke_token(token_jti)

# Emergency rate limit activation
>>> from app.extensions import limiter
>>> limiter.limit("1 per minute")(app)
```

## 📋 Security Checklist

### Pre-Deployment Security Checklist

- [ ] **Secrets Management**
  - [ ] All secrets are generated securely
  - [ ] No secrets in version control
  - [ ] Environment variables properly configured

- [ ] **Authentication**
  - [ ] JWT secrets are strong and unique
  - [ ] Token expiration times are appropriate
  - [ ] Password policies are enforced

- [ ] **Database Security**
  - [ ] Database credentials are secure
  - [ ] Database access is restricted
  - [ ] SSL/TLS is enabled for database connections

- [ ] **Network Security**
  - [ ] HTTPS is enforced
  - [ ] Security headers are configured
  - [ ] CORS is properly configured

- [ ] **Input Validation**
  - [ ] All inputs are validated
  - [ ] SQL injection prevention is in place
  - [ ] XSS protection is enabled

- [ ] **Monitoring**
  - [ ] Security logging is enabled
  - [ ] Error monitoring is configured
  - [ ] Intrusion detection is active

### Post-Deployment Security Checklist

- [ ] **Regular Updates**
  - [ ] Dependencies are regularly updated
  - [ ] Security patches are applied promptly
  - [ ] Security configurations are reviewed

- [ ] **Monitoring**
  - [ ] Security logs are regularly reviewed
  - [ ] Alerts are properly configured
  - [ ] Incident response procedures are tested

- [ ] **Backup & Recovery**
  - [ ] Backups are encrypted
  - [ ] Recovery procedures are tested
  - [ ] Data retention policies are enforced

## 📚 Security Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [JWT Security Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

### Tools
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://pyup.io/safety/) - Dependency vulnerability scanner
- [OWASP ZAP](https://www.zaproxy.org/) - Web application security scanner

### Security Services
- [Sentry](https://sentry.io/) - Error tracking and monitoring
- [Snyk](https://snyk.io/) - Vulnerability management
- [Auth0](https://auth0.com/) - Authentication as a service

---

Remember: Security is an ongoing process, not a one-time setup. Regularly review and update your security measures to protect against evolving threats.
