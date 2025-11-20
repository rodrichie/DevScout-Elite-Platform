# Security Guidelines

## Overview

This document outlines security best practices and configurations for the DevScout Elite Platform.

---

## Sensitive Information Protection

### Environment Variables

**Development Environment**:
- Default credentials in `.env.example` are for **development only**
- Never use default passwords in production
- Copy `.env.example` to `.env` and customize

**Production Environment**:
- Use **secrets management systems**: AWS Secrets Manager, Azure Key Vault, HashiCorp Vault
- Rotate credentials every 90 days
- Use strong, randomly generated passwords (32+ characters)
- Never commit `.env` files to git

### Generating Secure Secrets

```bash
# Generate secure random password
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate Fernet key for Airflow
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Authentication & Authorization

### JWT Tokens

**Configuration** (`api/middleware/auth.py`):
- Token expiry: 30 minutes (configurable)
- Algorithm: HS256
- Secret key: Must be set via `JWT_SECRET_KEY` environment variable

**Production Checklist**:
- [ ] Generate unique JWT secret key
- [ ] Set `JWT_SECRET_KEY` in environment
- [ ] Enable HTTPS/TLS
- [ ] Configure token refresh mechanism
- [ ] Implement token blacklisting for logout

### User Authentication

**Default Users** (Development Only):
- `admin` / `secret` - Full administrative access
- `recruiter` / `secret` - Read-only access

**Production Requirements**:
- Replace fake user database with real database
- Implement proper user registration
- Use bcrypt for password hashing (already configured)
- Add multi-factor authentication (MFA)
- Implement account lockout after failed attempts

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **admin** | Full CRUD access to all endpoints |
| **recruiter** | Read-only access to candidates, skills, analytics |
| **user** | Limited read access |

---

## Database Security

### Connection Security

**Current Implementation**:
```python
# All database connections use environment variables
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'postgres'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)
```

**Production Checklist**:
- [ ] Use SSL/TLS for database connections
- [ ] Enable PostgreSQL SSL mode: `sslmode=require`
- [ ] Use connection pooling with authentication
- [ ] Implement database firewall rules
- [ ] Restrict database access to application subnet only

### SQL Injection Prevention

- **Parameterized Queries**: All SQL queries use parameterized statements
- **ORM Usage**: Consider SQLAlchemy for additional protection
- **Input Validation**: Pydantic models validate all API inputs

### Data Encryption

**At Rest**:
- Enable PostgreSQL encryption at rest
- Encrypt MinIO buckets
- Use encrypted volumes in cloud deployments

**In Transit**:
- TLS 1.3 for all connections
- HTTPS for API endpoints
- Encrypted database connections

---

## API Security

### HTTPS/TLS

**Production Configuration**:
```yaml
# nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/devscout.crt;
    ssl_certificate_key /etc/ssl/private/devscout.key;
    ssl_protocols TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### CORS Configuration

**Current Settings** (`api/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # CHANGE IN PRODUCTION
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Settings**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://devscout.com",
        "https://app.devscout.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Rate Limiting

**Implementation Needed** (Future Enhancement):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/candidates")
@limiter.limit("100/minute")
async def get_candidates():
    pass
```

---

## Secrets in Docker Compose

### Current Configuration

**Development** (`docker-compose.yml`):
- Uses plain environment variables
- Acceptable for local development
- NOT suitable for production

**Production** (Use Docker Secrets):
```yaml
services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password

secrets:
  postgres_password:
    external: true
```

### Kubernetes Secrets

**Example Kubernetes Secret**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: devscout-secrets
type: Opaque
data:
  postgres-password: <base64-encoded>
  jwt-secret: <base64-encoded>
  github-token: <base64-encoded>
```

**Usage in Deployment**:
```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: devscout-secrets
        key: postgres-password
```

---

## Third-Party API Keys

### GitHub Token

**Current Usage**:
- Optional for development
- Required for production to avoid rate limits
- Stored in `GITHUB_TOKEN` environment variable

**Security Requirements**:
- Use GitHub Personal Access Token (PAT)
- Grant minimal permissions (read-only public repos)
- Rotate tokens every 90 days
- Monitor token usage in GitHub settings

**Token Permissions**:
- `public_repo`: Read-only access to public repositories
- `user:email`: Read user email addresses (optional)

---

## Monitoring & Auditing

### Security Logging

**What to Log**:
- Authentication attempts (success/failure)
- API access with user context
- Database queries (slow queries, errors)
- Unauthorized access attempts

**Example Implementation**:
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/auth/token")
async def login(form_data: OAuth2PasswordRequestForm):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt: {form_data.username}")
        raise HTTPException(status_code=401)
    
    logger.info(f"Successful login: {user['username']}")
    return {"access_token": create_token(user)}
```

### Security Monitoring

**Prometheus Metrics**:
- Failed authentication rate
- API error rates
- Database connection failures
- Suspicious activity patterns

**Grafana Alerts**:
- Alert on high authentication failure rate
- Alert on unusual API access patterns
- Alert on database connection anomalies

---

## Vulnerability Management

### Dependency Scanning

**Tools**:
- `pip-audit`: Scan Python dependencies for known CVEs
- `safety`: Check for security vulnerabilities
- GitHub Dependabot: Automatic dependency updates

**Run Security Scans**:
```bash
# Install pip-audit
pip install pip-audit

# Scan for vulnerabilities
pip-audit -r requirements.txt

# Use safety
pip install safety
safety check -r requirements.txt
```

### Container Security

**Best Practices**:
- Use official base images
- Scan images with Trivy or Clair
- Update base images regularly
- Run containers as non-root user
- Use minimal images (alpine when possible)

**Example Dockerfile Security**:
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "main:app"]
```

---

## Compliance & Data Privacy

### GDPR Compliance

**Personal Data Handling**:
- Candidate names, emails, phone numbers are PII
- Implement data retention policies
- Provide data export functionality
- Implement right to be forgotten (deletion)

**Required Features**:
- [ ] Data anonymization for analytics
- [ ] Audit logs for data access
- [ ] Consent management
- [ ] Data export API

### Data Retention

**Policy**:
- Resume files: 1 year
- Candidate records: 2 years from last update
- Audit logs: 7 years
- Analytics data: Aggregated, anonymized

---

## Incident Response

### Security Incident Checklist

1. **Detect**: Monitor logs and alerts
2. **Contain**: Isolate affected systems
3. **Investigate**: Analyze logs and access patterns
4. **Remediate**: Patch vulnerabilities, rotate credentials
5. **Document**: Record incident details and response
6. **Review**: Post-mortem and improve security

### Emergency Contacts

- Security Team: security@devscout.com
- DevOps Team: devops@devscout.com
- On-Call Engineer: [PagerDuty/Slack]

---

## Security Checklist for Production

### Infrastructure
- [ ] Enable HTTPS/TLS everywhere
- [ ] Configure firewall rules
- [ ] Use private subnets for databases
- [ ] Enable VPC/network isolation
- [ ] Set up WAF (Web Application Firewall)

### Authentication
- [ ] Generate unique JWT secret key
- [ ] Implement token refresh mechanism
- [ ] Add MFA for admin accounts
- [ ] Replace fake user database with real DB
- [ ] Implement password complexity requirements

### Secrets Management
- [ ] Move all secrets to secrets manager
- [ ] Rotate all default credentials
- [ ] Use IAM roles instead of access keys
- [ ] Enable secret rotation policies

### Monitoring
- [ ] Set up security alerts
- [ ] Enable audit logging
- [ ] Configure SIEM integration
- [ ] Set up intrusion detection

### Compliance
- [ ] Document data flows
- [ ] Implement data retention policies
- [ ] Add privacy policy
- [ ] Conduct security audit

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-11-20  
**Security Contact**: security@devscout.com
