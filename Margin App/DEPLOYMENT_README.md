# Margin App - Simple AWS Deployment

## Quick Setup

### 1. Prerequisites
- AWS CLI configured
- Terraform installed
- AWS Key Pair created
- Git repository uploaded

### 2. Authentication Setup
**Login credentials:**
- Username: `admin`
- Password: `password123`

### 3. Local Testing
```bash
cd "Margin App"
docker-compose up
# Access: http://localhost
```

### 4. AWS Deployment
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

### 5. Files Created
```
Margin App/
├── Dockerfile                 # Container configuration
├── docker-compose.yml        # Multi-container setup
├── nginx.conf                # Reverse proxy config
├── requirements.txt          # Python dependencies
├── auth/
│   └── .htpasswd             # Basic auth credentials
└── terraform/
    ├── main.tf               # Infrastructure code
    ├── variables.tf          # Input variables
    └── terraform.tfvars.example
```

### 6. Post-Deployment Access

#### Option A: Direct IP Access
```bash
# Get the public IP from Terraform output
terraform output instance_ip
# Example output: 54.123.456.789

# Access via browser:
http://54.123.456.789
```

#### Option B: Domain Setup
1. **Get Public IP from Terraform:**
   ```bash
   terraform output instance_ip
   # Copy the IP address (e.g., 54.123.456.789)
   ```

2. **Add DNS A Record:**
   - Go to your domain registrar (GoDaddy, Cloudflare, etc.)
   - Add an A record:
     ```
     Type: A
     Name: margin (or @ for root domain)
     Value: 54.123.456.789
     TTL: 300 (5 minutes)
     ```

3. **Access Options:**
   ```
   http://margin.yourdomain.com    # If using subdomain
   http://yourdomain.com           # If using root domain
   ```

#### Authentication Flow:
- **With Authentication**: `http://your-domain.com` → Nginx → Login → Streamlit App
- **Without Authentication**: `http://your-domain.com:8501` → Direct Streamlit Access

#### Port Configuration:
- **Port 80**: Nginx proxy with HTTP Basic Auth (recommended)
- **Port 8501**: Direct Streamlit access (no authentication)
- **Port 22**: SSH access for server management

⚠️ **Security Note**: In production, port 8501 should be blocked in security groups to force authentication through Nginx.

### 7. Optional: SSL/HTTPS Setup (for domains)

#### If you have a domain, you can add HTTPS:

1. **SSH into your EC2 instance:**
   ```bash
   ssh -i your-key.pem ec2-user@54.123.456.789
   ```

2. **Install Certbot:**
   ```bash
   sudo yum install -y certbot python3-certbot-nginx
   ```

3. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Auto-renewal setup:**
   ```bash
   sudo crontab -e
   # Add this line:
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

5. **Update Security Group:**
   ```bash
   # Add HTTPS port 443 to terraform/main.tf
   ingress {
     from_port   = 443
     to_port     = 443
     protocol    = "tcp"
     cidr_blocks = ["0.0.0.0/0"]
   }
   ```

After SSL setup:
- **Secure access**: `https://yourdomain.com`
- **HTTP redirects**: `http://yourdomain.com` → `https://yourdomain.com`

### 8. Key Changes Made
- ✅ Fixed Windows path in Margin_App.py:34
- ✅ Created requirements.txt for container
- ✅ Set up basic HTTP authentication
- ✅ Configured for us-east-1 region
- ✅ Minimal Terraform with t2.micro instance