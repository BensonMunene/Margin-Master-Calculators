# ETF Returns Viz Django App - Deployment Plan

## Overview
Deploy Django Returns Viz app on AWS EC2 t2.micro with Docker, Nginx authentication, and SSL.

## AWS Infrastructure
- **EC2**: t2.micro instance (Free Tier)
- **Storage**: 20GB EBS root volume
- **Security Group**: Ports 22, 80, 443 (restricted to team IPs)
- **Elastic IP**: For consistent access

## Docker Setup

### Dockerfile
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "returns_viz.wsgi:application"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=*
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./.htpasswd:/etc/nginx/.htpasswd
    depends_on:
      - app
    restart: unless-stopped
```

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream django {
        server app:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Deployment Steps

### 1. Launch EC2 Instance
- Amazon Linux 2 AMI
- t2.micro instance type
- Configure security group
- Create/select key pair

### 2. Server Setup
```bash
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Docker
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Re-login for group changes
exit
```

### 3. Deploy Application
```bash
ssh -i your-key.pem ec2-user@your-instance-ip

# Clone repo
git clone <repository-url>
cd "Margin-Master-Calculators/Returns Viz App/Django App/"

# Create password file
sudo yum install -y httpd-tools
htpasswd -c .htpasswd teamuser1
htpasswd .htpasswd teamuser2

# Deploy
docker-compose up -d
```

### 4. SSL Setup (Optional)
```bash
sudo yum install -y certbot
docker-compose stop nginx
sudo certbot certonly --standalone -d your-domain.com
# Update nginx.conf with SSL configuration
docker-compose up -d nginx
```

## Authentication
- **Layer 1**: Nginx basic auth (password prompt)
- **Layer 2**: Django CSRF protection

## Maintenance
```bash
# View logs
docker-compose logs -f

# Update app
git pull
docker-compose up -d --build

# Restart
docker-compose restart
```

## Cost
~$14/month (covered by AWS $200 credits)

---
**Status**: Ready for deployment