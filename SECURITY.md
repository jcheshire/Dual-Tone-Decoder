# Security Measures

This document outlines the security measures implemented in the Dual-Tone Decoder application.

## Implemented Security Controls

### 1. File Upload Security

**Path Traversal Prevention:**
- Filename sanitization using `os.path.basename()` to strip directory components
- UUID-based filename generation (user input never used in file paths)
- Path validation to ensure files stay within upload directory
- Strict file extension whitelist (`.wav` only)

**File Size Limits:**
- Maximum file size: 50MB (configurable)
- Chunked reading (1MB chunks) to prevent memory exhaustion
- Size validation during upload, not just header check

**File Type Validation:**
- Extension whitelist hardcoded in application (not user-configurable)
- Only `.wav` files accepted
- Content-type validation by audio processing libraries

### 2. Rate Limiting

**API Endpoints Protected:**
- Audio upload: 10 requests/minute per IP
- Tone entry creation: 30 requests/minute per IP
- Tone entry deletion: 30 requests/minute per IP
- Health check: 60 requests/minute per IP

**Implementation:**
- Uses SlowAPI library with IP-based rate limiting
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Prevents DoS attacks and resource exhaustion

### 3. Input Validation

**Tone Entry Labels:**
- HTML/script tag removal to prevent XSS
- Non-printable character filtering
- Length limits: 1-255 characters
- Whitespace normalization

**Frequency Values:**
- Range validation: 20Hz - 20kHz (human audio range)
- Type validation: must be positive floats
- Prevents extreme values that could cause processing issues

**Query Parameters:**
- Skip parameter: capped at 0 minimum
- Limit parameter: capped at 1000 maximum
- Prevents excessive database queries

### 4. SQL Injection Prevention

**Protected by Design:**
- SQLAlchemy ORM with parameterized queries
- No raw SQL string concatenation
- All database queries use bound parameters
- ✅ No additional measures needed

### 5. Error Message Sanitization

**Information Disclosure Prevention:**
- Generic error messages returned to users
- Internal errors logged (TODO: implement logging)
- No stack traces or paths exposed
- No library version information leaked

### 6. Temporary File Management

**Secure Handling:**
- Files deleted after processing in finally block
- Unique UUID filenames prevent conflicts
- Upload directory isolated from application code
- Failed cleanups don't crash the application

### 7. Database Security

**Protection Measures:**
- SQLite database in application directory
- Not web-accessible (backend only)
- Async queries prevent blocking
- Transaction-based updates for consistency

## Known Limitations

### Authentication/Authorization

**Current State: NO AUTHENTICATION**

The application currently has **no authentication or authorization**. This means:

- ⚠️ Anyone can upload audio files
- ⚠️ Anyone can create/modify/delete tone table entries
- ⚠️ No user accounts or API keys
- ⚠️ No access logs for auditing

**Recommendations:**

If deploying publicly or in a multi-user environment, consider adding:

1. **Basic Authentication** - HTTP Basic Auth via NGINX
2. **API Keys** - Token-based authentication
3. **User Accounts** - Full user management system
4. **IP Whitelisting** - Restrict access to known IPs via NGINX

**Example NGINX Basic Auth:**
```nginx
location /api/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8001;
}
```

### CORS (Cross-Origin Resource Sharing)

**Current State: NOT CONFIGURED**

If accessing the API from a browser on a different domain:

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Content Security Policy

**Current State: NOT CONFIGURED**

Add CSP headers via NGINX for defense-in-depth:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self';";
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### HTTPS/TLS

**Current State: HTTP ONLY (unless configured)**

Production deployments MUST use HTTPS:

```bash
sudo certbot --nginx -d dualtone.joshcheshire.com
```

Enforces:
- Encrypted traffic
- Certificate validation
- Protection against MITM attacks

## Monitoring & Logging

### TODO: Implement Logging

Currently missing:
- Access logs for API requests
- Error logging for debugging
- Audit trail for tone table changes
- Failed login attempts (when auth added)

**Recommended:** Add Python logging to track:
- File uploads (IP, size, result)
- Database modifications
- Rate limit violations
- Processing errors

### Monitoring Upload Directory

**Recommended Cron Job:**
```bash
# Clean up orphaned files older than 1 hour
0 * * * * find /path/to/uploads -type f -mmin +60 -delete
```

## Security Checklist for Deployment

- [ ] Configure HTTPS with Let's Encrypt
- [ ] Add authentication (Basic Auth or API keys)
- [ ] Configure NGINX security headers
- [ ] Set up IP whitelisting if internal use
- [ ] Implement application logging
- [ ] Set up log rotation
- [ ] Configure automated backups of tone_decoder.db
- [ ] Set up monitoring/alerting
- [ ] Review and adjust rate limits based on usage
- [ ] Configure firewall (ufw) to only allow 80/443
- [ ] Disable directory listing in NGINX
- [ ] Run backend as non-root user (systemd service)
- [ ] Set proper file permissions (uploads dir 755, db 664)
- [ ] Configure automated security updates

## Reporting Security Issues

If you discover a security vulnerability:

1. Do NOT open a public GitHub issue
2. Email: [your-security-email@domain.com]
3. Include: description, reproduction steps, impact
4. Allow 48 hours for response before disclosure

## Security Update Policy

- Critical vulnerabilities: Patch within 24 hours
- High severity: Patch within 7 days
- Medium/Low: Patch in next release
- Dependency updates: Monthly review

## Compliance Notes

This application:
- Does NOT store PII (personally identifiable information)
- Does NOT use cookies or tracking
- Does NOT share data with third parties
- Audio files are processed and immediately deleted
- Tone table data is user-provided, not sensitive

If your use case involves processing sensitive audio:
- Add encryption at rest for database
- Consider memory wiping for temporary files
- Implement audit logging
- Add user consent mechanisms
