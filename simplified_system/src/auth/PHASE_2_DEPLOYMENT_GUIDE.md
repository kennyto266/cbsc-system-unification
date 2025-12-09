# Phase 2 Source Authentication Layer - Deployment Guide
# 阶段2源认证层 - 部署指南

**Version:** 2.0.0
**Deployment Date:** 2025-01-28
**Security Classification:** CONFIDENTIAL

## 🚀 Quick Start

### **1. Installation**
```bash
# Navigate to the simplified system directory
cd simplified_system

# Install Phase 2 dependencies
pip install -r src/auth/requirements_phase2.txt

# Verify installation
python -c "from src.auth.phase2_integration import get_phase2_authentication; print('✅ Phase 2 Authentication Ready')"
```

### **2. Basic Usage**
```python
from simplified_system.src.auth import get_phase2_authentication

# Initialize authentication
auth = get_phase2_authentication()

# Authenticate HKMA data
result = await auth.authenticate_hkma_data(
    data={"hibor_rate": 3.15, "source": "hkma.gov.hk"},
    data_id="hibor_20240128"
)

if result.overall_verdict.value == "AUTHENTIC":
    print("✅ Data authenticated successfully")
else:
    print(f"❌ Authentication failed: {result.error_message}")
```

## 📋 System Requirements

### **Minimum Requirements**
- **Python:** 3.9 or higher
- **Memory:** 512MB available RAM
- **Storage:** 100MB free space
- **Network:** Internet access for certificate validation

### **Recommended Requirements**
- **Python:** 3.11 or higher
- **Memory:** 1GB available RAM
- **Storage:** 500MB free space
- **Network:** Stable internet connection
- **CPU:** Multi-core processor for parallel verification

## 🔧 Installation Steps

### **Step 1: Environment Setup**
```bash
# Create virtual environment (recommended)
python -m venv auth_env
source auth_env/bin/activate  # On Windows: auth_env\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### **Step 2: Install Dependencies**
```bash
# Install Phase 2 specific dependencies
pip install cryptography>=41.0.0
pip install PyJWT>=2.8.0
pip install PyYAML>=6.0
pip install dnspython>=2.4.0
pip install requests>=2.31.0

# Or install from requirements file
pip install -r src/auth/requirements_phase2.txt
```

### **Step 3: Configuration Setup**
```bash
# Create configuration directories
mkdir -p config/auth/keys
mkdir -p config/auth/certificates
mkdir -p config/auth/whitelist

# Copy default configuration
cp src/auth/config/phase2_authentication_config.yaml config/auth/
```

### **Step 4: Certificate Setup**
```bash
# Download trusted certificates (production)
# For HKMA APIs, download from: https://www.hkma.gov.hk/

# Example: Add HKMA certificate
wget -O config/auth/certificates/hkma.pem https://www.hkma.gov.hk/certificate.pem

# For development, you can create self-signed certificates
openssl req -x509 -newkey rsa:4096 -keyout config/auth/keys/test_key.pem -out config/auth/certificates/test_cert.pem -days 365 -nodes
```

### **Step 5: Key Management**
```bash
# Generate RSA key pair for digital signatures
openssl genrsa -out config/auth/keys/private_key.pem 2048
openssl rsa -in config/auth/keys/private_key.pem -pubout -out config/auth/keys/public_key.pem

# Set appropriate permissions
chmod 600 config/auth/keys/private_key.pem
chmod 644 config/auth/keys/public_key.pem
```

## ⚙️ Configuration

### **Main Configuration File:** `config/auth/phase2_authentication_config.yaml`

#### **Digital Signature Configuration**
```yaml
digital_signature_verifier:
  enabled: true
  supported_algorithms: ["RS256", "ES256", "HS256"]
  key_store_path: "config/auth/keys/"
  trusted_issuers:
    - "hkma.gov.hk"
    - "api.hkma.gov.hk"

  # HMAC secret for internal APIs
  default_hmac_key: "your-secret-key-here"

  # Performance settings
  verification_timeout: 10.0
  max_signature_size: 8192
```

#### **TLS Certificate Configuration**
```yaml
tls_certificate_validator:
  enabled: true
  certificate_store_path: "config/auth/certificates/"
  critical_endpoints:
    - "api.hkma.gov.hk:443"
    - "18.180.162.113:9191"  # Note: HTTP only - security issue

  # Security settings
  validation_timeout: 30.0
  max_chain_length: 10
  allow_self_signed: false  # Set to true for development

  # Certificate pinning
  pinned_certificates:
    hkma_api: "base64-sha256-fingerprint-here"
```

#### **Endpoint Whitelist Configuration**
```yaml
endpoint_whitelist_verifier:
  enabled: true
  whitelist_path: "config/auth/whitelist.json"

  # Security settings
  block_private_ips: true
  block_suspicious_tlds: true
  enable_dns_validation: true

  # Pre-approved endpoints
  approved_endpoints:
    "api.hkma.gov.hk":
      owner: "Hong Kong Monetary Authority"
      purpose: "Financial data API"
      approved: true
      required_dns_records: ["A", "AAAA", "TXT"]
```

#### **Rate Limiting Configuration**
```yaml
rate_limit_anomaly_detector:
  enabled: true
  window_sizes: [60, 300, 900]  # 1min, 5min, 15min

  # Rate limits
  max_requests_per_window:
    60: 100    # 100 requests per minute
    300: 400   # 400 requests per 5 minutes
    900: 1000  # 1000 requests per 15 minutes

  # Response levels
  response_levels:
    warning: {threshold: 0.7, action: "log_warning"}
    throttle: {threshold: 0.85, action: "add_delay", delay_ms: 1000}
    block: {threshold: 1.0, action: "block_request"}
```

## 🔒 Security Setup

### **Certificate Pinning**
```python
# Calculate certificate fingerprint for pinning
import hashlib
import base64
from cryptography import x509

def calculate_certificate_fingerprint(cert_path):
    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())

    fingerprint = hashlib.sha256(cert.public_bytes_raw()).digest()
    return base64.b64encode(fingerprint).decode('ascii')

# Use this fingerprint in your configuration
fingerprint = calculate_certificate_fingerprint("config/auth/certificates/hkma.pem")
print(f"HKMA Certificate Fingerprint: {fingerprint}")
```

### **API Key Setup**
```python
# For internal API authentication
import os

# Set environment variables
os.environ['STOCK_API_SECRET'] = 'your-secure-secret-key'
os.environ['HKMA_API_KEY'] = 'your-hkma-api-key'

# Or use configuration file
config = {
    'digital_signature_verifier': {
        'hmac_secrets': {
            'stock_api': os.environ['STOCK_API_SECRET'],
            'hkma_api': os.environ['HKMA_API_KEY']
        }
    }
}
```

## 🧪 Testing

### **Run Unit Tests**
```bash
# Run all tests
python -m pytest src/auth/tests/test_phase2_source_authentication.py -v

# Run with coverage
python -m pytest src/auth/tests/ --cov=src/auth --cov-report=html

# Run specific test categories
python -m pytest src/auth/tests/ -k "test_digital_signature" -v
python -m pytest src/auth/tests/ -k "test_tls_certificate" -v
python -m pytest src/auth/tests/ -k "test_rate_limit" -v
```

### **Integration Testing**
```bash
# Test HKMA data authentication
python -c "
import asyncio
from simplified_system.src.auth import get_phase2_authentication

async def test_hkma():
    auth = get_phase2_authentication()
    result = await auth.authenticate_hkma_data(
        data={'source': 'hkma.gov.hk', 'hibor_rate': 3.15},
        data_id='test_hkma_001'
    )
    print(f'HKMA Authentication: {result.overall_verdict.value}')

asyncio.run(test_hkma())
"

# Test rate limiting
python -c "
import asyncio
from simplified_system.src.auth import get_phase2_authentication

async def test_rate_limit():
    auth = get_phase2_authentication()
    for i in range(5):
        result = await auth.authenticate_api_request(
            request_info={'endpoint': 'test.api.com'},
            request_id=f'test_req_{i}'
        )
        print(f'Request {i}: {result.overall_verdict.value}')

asyncio.run(test_rate_limit())
"
```

## 🚀 Deployment

### **Development Deployment**
```bash
# Start with development configuration
export ENVIRONMENT=development
python -m simplified_system.src.auth.phase2_integration

# Or run the demo
python src/auth/phase2_integration.py
```

### **Production Deployment**
```bash
# Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Use production configuration
cp config/auth/phase2_authentication_config.yaml config/auth/production_config.yaml
# Edit production_config.yaml with production settings

# Deploy with process manager (systemd example)
sudo tee /etc/systemd/quant-auth.service > /dev/null <<EOF
[Unit]
Description=Quantitative Trading Authentication Service
After=network.target

[Service]
Type=simple
User=quant
WorkingDirectory=/opt/quant/simplified_system
Environment=ENVIRONMENT=production
ExecStart=/opt/quant/venv/bin/python -m simplified_system.src.auth.auth_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable quant-auth
sudo systemctl start quant-auth
```

### **Docker Deployment**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY simplified_system/ .

RUN pip install -r src/auth/requirements_phase2.txt

EXPOSE 8000
CMD ["python", "-m", "simplified_system.src.auth.auth_server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  auth-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./config/auth:/app/config/auth
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📊 Monitoring

### **Health Check Endpoint**
```bash
# Check service health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "verifiers": {
    "digital_signature": {"status": "healthy"},
    "tls_certificate": {"status": "healthy"},
    "endpoint_whitelist": {"status": "healthy"},
    "rate_limit": {"status": "healthy"}
  },
  "statistics": {
    "total_verifications": 1250,
    "success_rate": 0.98
  }
}
```

### **Statistics Endpoint**
```bash
# Get authentication statistics
curl http://localhost:8000/stats

# Performance metrics
curl http://localhost:8000/metrics
```

### **Log Monitoring**
```bash
# View authentication logs
tail -f logs/authentication.log

# Monitor for security events
grep "SECURITY" logs/authentication.log
```

## 🔧 Troubleshooting

### **Common Issues**

#### **Certificate Validation Failures**
```bash
# Check certificate validity
openssl x509 -in config/auth/certificates/hkma.pem -text -noout

# Test TLS connection
openssl s_client -connect api.hkma.gov.hk:443 -servername api.hkma.gov.hk
```

#### **DNS Resolution Issues**
```bash
# Test DNS resolution
nslookup api.hkma.gov.hk
dig api.hkma.gov.hk

# Check DNS records
dig api.hkma.gov.hk A
dig api.hkma.gov.hk TXT
```

#### **Rate Limiting Issues**
```bash
# Check rate limit statistics
python -c "
import json
from pathlib import Path
stats = json.loads(Path('config/auth/rate_limit_stats.json').read_text())
print(json.dumps(stats, indent=2))
"
```

#### **Performance Issues**
```bash
# Profile authentication performance
python -m cProfile -o profile.stats src/auth/phase2_integration.py

# Analyze results
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(10)
"
```

### **Error Codes**

| Error Code | Description | Solution |
|------------|-------------|----------|
| AUTH_001 | Digital signature verification failed | Check key configuration |
| AUTH_002 | TLS certificate validation failed | Update certificates |
| AUTH_003 | Endpoint not whitelisted | Add to whitelist or approval queue |
| AUTH_004 | Rate limit exceeded | Wait or adjust rate limits |
| AUTH_005 | Configuration error | Check YAML syntax and paths |

## 📋 Maintenance

### **Regular Tasks**
- **Certificate Renewal:** Monitor expiration dates and renew certificates
- **Key Rotation:** Rotate private keys regularly (recommended every 90 days)
- **Configuration Updates:** Review and update whitelists and rate limits
- **Log Analysis:** Monitor authentication logs for security events

### **Backup Strategy**
```bash
# Backup configuration
tar -czf auth_backup_$(date +%Y%m%d).tar.gz config/auth/

# Backup logs
tar -czf auth_logs_$(date +%Y%m%d).tar.gz logs/

# Automate with cron
0 2 * * 0 tar -czf /backup/auth_$(date +\%Y\%m\%d).tar.gz config/auth/ logs/
```

## 🆘 Support

### **Getting Help**
1. **Check logs:** `logs/authentication.log`
2. **Run health check:** `/health` endpoint
3. **Review configuration:** `config/auth/phase2_authentication_config.yaml`
4. **Run diagnostics:** `python src/auth/diagnostics.py`

### **Contact Information**
- **Documentation:** `src/auth/README.md`
- **Issues:** Create issue in project repository
- **Security:** Report security issues through secure channels

---

**✅ DEPLOYMENT COMPLETE**

The Phase 2 Source Authentication Layer is now deployed and ready to secure your quantitative trading system data sources.

**Next Steps:**
1. Monitor authentication performance
2. Address identified security issues (HTTPS upgrade)
3. Plan Phase 3 advanced security features

**Security Classification:** CONFIDENTIAL