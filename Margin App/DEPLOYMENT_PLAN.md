# Margin Master Calculators - Deployment Plan

## 1. Project Overview

**Application**: Professional ETF Margin Trading Calculator
**Technology Stack**: Streamlit, Python, Pandas, Plotly
**Target Environment**: AWS EC2 with Docker containerization

## 2. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud Infrastructure                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    EC2 Instance                             │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │                  Docker Host                            │ │ │
│  │  │                                                         │ │ │
│  │  │  ┌─────────────────┐  ┌─────────────────┐               │ │ │
│  │  │  │  Nginx Container│  │  Streamlit      │               │ │ │
│  │  │  │                 │  │  Container      │               │ │ │
│  │  │  │  - Reverse      │  │                 │               │ │ │
│  │  │  │    Proxy        │  │  - Streamlit    │               │ │ │
│  │  │  │  - SSL          │  │    App (8501)   │               │ │ │
│  │  │  │  - Basic Auth   │  │  - Python deps  │               │ │ │
│  │  │  │  - Port 80/443  │  │  - CSV Data     │               │ │ │
│  │  │  └─────────────────┘  └─────────────────┘               │ │ │
│  │  │                                                         │ │ │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  │               Logs Volume                           │ │ │
│  │  │  │                                                     │ │ │
│  │  │  │  - App Logs                                         │ │ │
│  │  │  │  - Access Logs                                      │ │ │
│  │  │  │  - Error Logs                                       │ │ │
│  │  │  └─────────────────────────────────────────────────────┘ │ │
│  │  │                                                         │ │ │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  │          CloudWatch Agent                          │ │ │
│  │  │  │  - System metrics collection                       │ │ │
│  │  │  │  - Log streaming to CloudWatch                     │ │ │
│  │  │  │  - Custom application metrics                      │ │ │
│  │  │  └─────────────────────────────────────────────────────┘ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     Security Groups                         │ │
│  │  - Port 22 (SSH) - Restricted to specific IPs              │ │
│  │  - Port 80 (HTTP) - Internal team access only              │ │
│  │  - Port 443 (HTTPS) - Internal team access only            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     EBS Storage                              │ │
│  │  - Root Volume (20GB) - Complete system storage             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Logs & Metrics
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS CloudWatch Services                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  CloudWatch     │  │  CloudWatch     │  │  CloudWatch     │ │
│  │  Logs           │  │  Metrics        │  │  Alarms         │ │
│  │                 │  │                 │  │                 │ │
│  │  - App Logs     │  │  - CPU Usage    │  │  - High Error   │ │
│  │  - Access Logs  │  │  - Memory Usage │  │    Rate         │ │
│  │  - Error Logs   │  │  - Disk Usage   │  │  - Low Uptime   │ │
│  │  - System Logs  │  │  - Network I/O  │  │  - High CPU     │ │
│  │                 │  │  - Uptime       │  │  - Disk Full    │ │
│  │                 │  │  - HTTP Status  │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   CloudWatch Dashboard                      │ │
│  │  - Real-time monitoring                                     │ │
│  │  - Custom metrics visualization                             │ │
│  │  - Alert status overview                                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Infrastructure Components

### 3.1 AWS Resources

- **EC2 Instance**: t2.micro (1 vCPU, 1GB RAM) - Free Tier eligible
- **Security Groups**: Restricted access for internal team
- **EBS Volume**: 
  - Root: 20GB gp2 (includes app, data, and logs) - Free Tier eligible
- **Elastic IP**: Static IP for domain mapping
- **VPC**: Default VPC with public subnet
- **CloudWatch**: Logging, metrics, and monitoring
- **IAM Roles**: EC2 instance profile for CloudWatch access

### 3.2 Docker Containers

#### Application Container
- **Base Image**: python:3.11-slim
- **Services**:
  - Streamlit app on port 8501
- **Data**: 
  - CSV and Excel files embedded in container
  - No persistent volumes needed
- **Volumes**: 
  - `/app/logs` - Application logs (optional)

#### Nginx Container
- **Base Image**: nginx:alpine
- **Configuration**:
  - Reverse proxy to Streamlit container
  - Basic HTTP authentication
  - SSL termination (Let's Encrypt)
  - Rate limiting
  - Access logging

## 4. Deployment Process

### 4.1 Infrastructure Setup (Terraform)

**Key Terraform Resources:**
- **EC2 Instance** with IAM role for CloudWatch access
- **Security Groups** for restricted internal team access
- **IAM Role & Instance Profile** for CloudWatch permissions
- **CloudWatch Log Groups** for different log types (app, nginx, system)
- **CloudWatch Alarms** for CPU, memory, disk, and error monitoring
- **SNS Topic & Email Alerts** for notifications
- **CloudWatch Dashboard** for real-time monitoring

**Important Configuration Points:**
- Instance gets `CloudWatchAgentServerPolicy` permissions
- Log groups with retention policies (7-14 days)
- Alarms trigger at 80% CPU, 85% memory, 80% disk usage
- Email notifications for all alerts
- Dashboard shows EC2 metrics, app metrics, and recent errors

### 4.2 Container Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "Margin_App.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    # Data files embedded in container - no volume mount needed
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### 4.3 Nginx Configuration
```nginx
events {
    worker_connections 1024;
}

http {
    upstream streamlit_app {
        server app:8501;
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        
        # Basic authentication
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        # Streamlit app
        location / {
            proxy_pass http://streamlit_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

## 5. Deployment Steps

### 5.1 Initial Setup
1. **Terraform Infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

2. **EC2 Instance Setup**:
   ```bash
   # SSH into EC2 instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Install Docker and Docker Compose
   sudo yum update -y
   sudo yum install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -a -G docker ec2-user
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Application Deployment**:
   ```bash
   # Clone repository
   git clone <repository-url>
   cd Margin-Master-Calculators/Margin App/
   
   # Build and run containers
   docker-compose up -d
   ```

### 5.2 Authentication Setup
```bash
# Create basic auth file (in project directory)
htpasswd -c .htpasswd teamuser1
htpasswd .htpasswd teamuser2
htpasswd .htpasswd teamuser3
htpasswd .htpasswd teamuser4
htpasswd .htpasswd teamuser5

# The nginx.conf already references this file
# When someone visits the link, they'll get a login popup
```

### 5.3 IP Whitelist (Optional Extra Security)
```bash
# In Terraform security group, restrict to specific IPs
ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = [
    "1.2.3.4/32",    # Office IP
    "5.6.7.8/32",    # Home IP 1
    "9.10.11.12/32"  # Home IP 2
  ]
}
```

### 5.3 SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo yum install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 6. Monitoring and Maintenance

### 6.1 CloudWatch Monitoring & Metrics

**System Metrics:**
- CPU Utilization (threshold: 80%)
- Memory Usage (threshold: 85%)
- Disk Space (threshold: 80%)
- Network I/O

**Application Metrics:**
- Request Count
- Error Rate (threshold: 10 errors/5min)
- Response Time
- Uptime Status

**Log Streams:**
- Streamlit logs → `/aws/ec2/margin-app/streamlit`
- Nginx access logs → `/aws/ec2/margin-app/nginx/access`
- Nginx error logs → `/aws/ec2/margin-app/nginx/error`
- System logs → `/aws/ec2/margin-app`

**Alerting:**
- SNS email notifications for all threshold breaches
- CloudWatch Dashboard for real-time monitoring
- Log retention: 7-14 days based on log type

### 6.3 Backup Strategy
- **Root Volume**: Daily snapshots of EBS volume
- **Application Code**: Git repository backup
- **Data**: Included in git repository (CSV/Excel files)

## 7. Security Considerations

### 7.1 Current Security Measures
- **Network Security**: Security groups restricting access to specific IP addresses
- **Authentication**: Multi-layer authentication system
  - Nginx basic auth (first layer)
  - Streamlit authentication (second layer)
- **Access Control**: Link-based access prevention
- **SSL/TLS**: HTTPS encryption for all traffic
- **SSH Access**: Key-based authentication only

### 7.2 Security Best Practices
- Regular security updates
- Firewall configuration
- Access logging and monitoring
- Secure secret management

## 8. Future Enhancements

### 8.1 Phase 2 Features
- **Advanced Authentication**: OAuth2/SAML integration
- **User Management**: Role-based access control
- **Enhanced Data**: API integration for real-time data
- **Caching**: Redis for session management
- **CloudWatch Agent**: Install and configure CloudWatch Agent for detailed system metrics

### 8.2 Phase 3 Features
- **CI/CD Pipeline**: GitHub Actions deployment
- **Load Balancing**: Multiple instance deployment
- **Auto Scaling**: Based on usage metrics
- **Monitoring**: CloudWatch, Prometheus, Grafana

### 8.3 Phase 4 Features
- **High Availability**: Multi-AZ deployment
- **CDN**: CloudFront for static assets
- **Data Storage**: S3 for historical data archives
- **Container Orchestration**: EKS/ECS migration

## 9. Cost Estimation

### 9.1 Monthly AWS Costs (Post-July 15, 2025 Free Tier)
**⚠️ Important**: AWS Free Tier changed on July 15, 2025

**New Credit System (Accounts created after July 15, 2025):**
- **Initial Credits**: $200 total ($100 at signup + $100 for completing activities)
- **Duration**: 6 months maximum OR until credits exhausted
- **t2.micro Cost**: ~$8.50/month (credits cover ~23 months of usage)
- **Total Coverage**: Full deployment FREE for 6+ months with $200 credits

**Estimated Monthly Costs with Credits:**
- **EC2 t2.micro**: $8.50/month (but covered by credits)
- **EBS Storage (20GB gp2)**: $2.00/month (but covered by credits)
- **CloudWatch Logs & Metrics**: $1-3/month (but covered by credits)
- **SNS Email Notifications**: $0/month (1000 free notifications)
- **Elastic IP**: $3.60/month (but covered by credits)
- **Data Transfer**: $1-2/month (but covered by credits)
- **Total**: $16-19/month (fully covered by $200 credits for 10+ months)

### 9.2 New Free Tier Strategy (Post-July 15, 2025)
- **Credit Management**: $200 credits last 10+ months for this deployment
- **Account Plan**: Choose "Free Plan" during AWS signup
- **Instance Type**: t2.micro sufficient for 5 concurrent users
- **Storage**: 20GB optimal for application needs
- **Monitoring**: Basic CloudWatch metrics included
- **Post Credits**: ~$16-19/month after credits exhausted
- **⚠️ Important**: AWS closes free accounts after 6 months - migrate to paid plan before expiration

## 10. Deployment Checklist

### 10.1 Pre-Deployment
- [ ] Terraform configuration reviewed
- [ ] Security groups configured
- [ ] SSH key pair created
- [ ] Domain DNS configured
- [ ] SSL certificates ready

### 10.2 Deployment
- [ ] Infrastructure provisioned
- [ ] Docker containers deployed
- [ ] Data files embedded in container
- [ ] Nginx configured and running
- [ ] SSL certificates installed
- [ ] Basic authentication configured

### 10.3 Post-Deployment
- [ ] Application accessibility tested
- [ ] Data files accessible in container
- [ ] Authentication working
- [ ] SSL certificate valid
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Team access verified

## 11. Troubleshooting Guide

### 11.1 Common Issues
- **Container startup failures**: Check logs with `docker-compose logs`
- **Nginx configuration errors**: Test with `nginx -t`
- **SSL certificate issues**: Verify certbot configuration
- **Authentication failures**: Check `.htpasswd` file permissions

### 11.2 Monitoring Commands
```bash
# Check container status
docker-compose ps

# View application logs
docker-compose logs app

# Monitor system resources
htop
df -h
```

---

**Document Version**: 1.0
**Created**: 2025-01-18
**Last Updated**: 2025-01-18
**Status**: Ready for Implementation