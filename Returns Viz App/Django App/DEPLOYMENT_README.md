# ETF Returns Viz Django App - Deployment Guide

This guide provides step-by-step instructions for deploying the ETF Returns Viz Django application on AWS EC2 using Docker and Terraform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Infrastructure Setup](#aws-infrastructure-setup)
3. [EC2 Instance Configuration](#ec2-instance-configuration)
4. [Application Deployment](#application-deployment)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Cost Estimation](#cost-estimation)

## Prerequisites

### Local Machine Requirements

- AWS CLI configured with appropriate credentials
- Terraform installed (v1.0+)
- SSH key pair for EC2 access
- Git

### AWS Account Requirements

- AWS account with EC2, VPC, and CloudWatch permissions
- $200 AWS credits (covers ~10-12 months of operation)

## AWS Infrastructure Setup

### 1. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region = "us-east-1"
key_pair_name = "your-key-pair-name"

# Restrict access to your team's IPs
ssh_allowed_ips = ["YOUR.IP.HERE/32"]
http_allowed_ips = ["0.0.0.0/0"]  # Or restrict to team IPs
https_allowed_ips = ["0.0.0.0/0"]  # Or restrict to team IPs
```

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply
```

Save the outputs, especially:
- `instance_ip`: Public IP of your EC2 instance
- `ssh_command`: Command to SSH into the instance

## EC2 Instance Configuration

### 1. Connect to EC2 Instance

```bash
ssh -i your-key-pair.pem ec2-user@<instance_ip>
```

### 2. Run Initial Setup

```bash
# Download and run setup script
curl -O https://raw.githubusercontent.com/YOUR_REPO/setup-ec2.sh
chmod +x setup-ec2.sh
./setup-ec2.sh

# Log out and back in for Docker permissions
exit
ssh -i your-key-pair.pem ec2-user@<instance_ip>
```

### 3. Clone Repository

```bash
cd /home/ec2-user
git clone <your-repository-url> etf-returns-viz
cd etf-returns-viz/Returns\ Viz\ App/Django\ App/
```

## Application Deployment

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with production values
nano .env
```

Required environment variables:
```
SECRET_KEY=<generate-a-secure-key>
DEBUG=False
ALLOWED_HOSTS=<your-ec2-ip>,<your-domain>
FMP_API_KEY=<your-fmp-api-key>
```

### 2. Set Up Authentication

```bash
# Create first user
htpasswd -c auth/.htpasswd admin

# Add additional users
htpasswd auth/.htpasswd user2
htpasswd auth/.htpasswd user3
```

### 3. Copy Data Files

If you have local data files:
```bash
# Copy from main Data directory
cp -r ../../Data/* Data/
```

### 4. Deploy Application

```bash
# Run deployment script
./deploy.sh
```

Or manually:
```bash
# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Verify Deployment

Access the application:
- URL: `http://<instance_ip>`
- You'll be prompted for username/password (from .htpasswd)

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install certbot
sudo yum install -y certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown ec2-user:ec2-user ssl/*

# Update nginx.conf (uncomment SSL section)
nano nginx.conf

# Restart nginx
docker-compose up -d nginx
```

### Option 2: Self-Signed (Development)

```bash
cd ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem
cd ..
```

## Monitoring & Maintenance

### CloudWatch Monitoring

The Terraform setup includes:
- CPU usage alarms (80% threshold)
- Disk usage alarms (80% threshold)
- Log groups for application, nginx, and system logs

### View Logs

```bash
# Application logs
docker-compose logs -f app

# Nginx logs
docker-compose logs -f nginx

# All logs
docker-compose logs -f
```

### Update Application

```bash
cd /home/ec2-user/etf-returns-viz/Returns\ Viz\ App/Django\ App/

# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Backup Database

```bash
# Create backup
docker-compose exec app python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Copy to S3 (if configured)
aws s3 cp backup_*.json s3://your-backup-bucket/
```

### Regular Maintenance

```bash
# Check disk space
df -h

# Clean up old Docker images
docker image prune -a

# Check container resource usage
docker stats
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs app

# Common fixes:
# - Check .env file exists and has correct values
# - Ensure static files directory exists
# - Check file permissions
```

#### 2. 502 Bad Gateway

```bash
# Check if Django app is running
docker-compose ps

# Check Django logs
docker-compose logs app

# Restart containers
docker-compose restart
```

#### 3. Permission Denied

```bash
# Fix Docker permissions
sudo usermod -a -G docker ec2-user
# Then log out and back in
```

#### 4. Static Files Not Loading

```bash
# Collect static files manually
docker-compose exec app python manage.py collectstatic --noinput

# Check nginx configuration
docker-compose exec nginx nginx -t
```

### Debug Commands

```bash
# Enter Django container
docker-compose exec app bash

# Run Django shell
docker-compose exec app python manage.py shell

# Check migrations
docker-compose exec app python manage.py showmigrations

# Test data loading
docker-compose exec app python manage.py test_data
```

## Cost Estimation

### AWS Free Tier (First 12 months)
- EC2 t2.micro: 750 hours/month free
- EBS storage: 30GB free
- Data transfer: 15GB free
- Total: $0/month

### Post Free Tier / With Credits
- EC2 t2.micro: ~$8.50/month
- EBS 20GB: ~$2.00/month
- Elastic IP: ~$3.60/month
- CloudWatch: ~$2.00/month
- **Total: ~$16/month** (covered by $200 credits for 12+ months)

### Cost Optimization Tips
1. Stop instance when not in use
2. Use CloudWatch to monitor usage
3. Set up billing alerts
4. Consider Reserved Instances for long-term use

## Security Best Practices

1. **Network Security**
   - Restrict security group IPs to team only
   - Use VPN for additional security
   - Enable AWS GuardDuty

2. **Application Security**
   - Keep SECRET_KEY secure
   - Use strong passwords in .htpasswd
   - Regularly update dependencies
   - Enable HTTPS with valid certificates

3. **Monitoring**
   - Set up CloudWatch alarms
   - Monitor access logs
   - Enable AWS CloudTrail

4. **Backup**
   - Regular database backups
   - EBS snapshot schedule
   - Test restore procedures

## Quick Reference

### Essential Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Restart application
docker-compose restart

# Update and restart
git pull && docker-compose up -d --build

# Create user
htpasswd auth/.htpasswd newuser

# Check status
docker-compose ps
```

### File Locations

- Application: `/home/ec2-user/etf-returns-viz/Returns Viz App/Django App/`
- Environment: `.env`
- Authentication: `auth/.htpasswd`
- SSL Certificates: `ssl/`
- Logs: `docker-compose logs`

### Support

For issues or questions:
1. Check application logs: `docker-compose logs app`
2. Check nginx logs: `docker-compose logs nginx`
3. Review this documentation
4. Check Django documentation: https://docs.djangoproject.com/

---

**Last Updated**: January 2025
**Version**: 1.0.