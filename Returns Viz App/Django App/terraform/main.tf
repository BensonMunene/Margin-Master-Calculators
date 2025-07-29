# Terraform configuration for ETF Returns Viz Django App deployment
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Security Group for Django App
resource "aws_security_group" "django_app_sg" {
  name        = "etf-returns-viz-sg"
  description = "Security group for ETF Returns Viz Django App"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips
    description = "SSH access"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.http_allowed_ips
    description = "HTTP access"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.https_allowed_ips
    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "etf-returns-viz-sg"
    Application = "ETF Returns Viz"
    Environment = var.environment
  }
}

# IAM Role for EC2 Instance (CloudWatch access)
resource "aws_iam_role" "ec2_cloudwatch_role" {
  name = "etf-returns-viz-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "etf-returns-viz-ec2-role"
    Application = "ETF Returns Viz"
  }
}

# Attach CloudWatch Agent policy to role
resource "aws_iam_role_policy_attachment" "cloudwatch_agent_policy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.ec2_cloudwatch_role.name
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "etf-returns-viz-ec2-profile"
  role = aws_iam_role.ec2_cloudwatch_role.name
}

# EC2 Instance
resource "aws_instance" "django_app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  vpc_security_group_ids = [aws_security_group.django_app_sg.id]

  # EBS root volume configuration
  root_block_device {
    volume_size = 30
    volume_type = "gp2"
    encrypted   = true
    
    tags = {
      Name        = "etf-returns-viz-root"
      Application = "ETF Returns Viz"
    }
  }

  # User data script to install Docker and Docker Compose
  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system
    yum update -y
    
    # Install Docker
    yum install -y docker git htop
    systemctl start docker
    systemctl enable docker
    usermod -a -G docker ec2-user
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Install CloudWatch Agent
    wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
    rpm -U ./amazon-cloudwatch-agent.rpm
    
    # Create directory for application
    mkdir -p /home/ec2-user/app
    chown ec2-user:ec2-user /home/ec2-user/app
    
    # Install httpd-tools for htpasswd
    yum install -y httpd-tools
  EOF

  tags = {
    Name        = "etf-returns-viz-server"
    Application = "ETF Returns Viz"
    Environment = var.environment
  }
}

# Elastic IP
resource "aws_eip" "django_app_eip" {
  instance = aws_instance.django_app.id
  domain   = "vpc"

  tags = {
    Name        = "etf-returns-viz-eip"
    Application = "ETF Returns Viz"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/etf-returns-viz/app"
  retention_in_days = 7

  tags = {
    Name        = "etf-returns-viz-app-logs"
    Application = "ETF Returns Viz"
  }
}

resource "aws_cloudwatch_log_group" "nginx_logs" {
  name              = "/aws/ec2/etf-returns-viz/nginx"
  retention_in_days = 7

  tags = {
    Name        = "etf-returns-viz-nginx-logs"
    Application = "ETF Returns Viz"
  }
}

resource "aws_cloudwatch_log_group" "system_logs" {
  name              = "/aws/ec2/etf-returns-viz/system"
  retention_in_days = 7

  tags = {
    Name        = "etf-returns-viz-system-logs"
    Application = "ETF Returns Viz"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "etf-returns-viz-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors cpu utilization"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    InstanceId = aws_instance.django_app.id
  }
}

resource "aws_cloudwatch_metric_alarm" "disk_usage" {
  alarm_name          = "etf-returns-viz-disk-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "disk_used_percent"
  namespace           = "CWAgent"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors disk usage"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    InstanceId = aws_instance.django_app.id
    path       = "/"
    device     = "xvda1"
    fstype     = "xfs"
  }
}

# Outputs
output "instance_ip" {
  value       = aws_eip.django_app_eip.public_ip
  description = "Public IP address of the EC2 instance"
}

output "instance_id" {
  value       = aws_instance.django_app.id
  description = "ID of the EC2 instance"
}

output "access_url" {
  value       = "http://${aws_eip.django_app_eip.public_ip}"
  description = "URL to access the application"
}

output "ssh_command" {
  value       = "ssh -i ${var.key_pair_name}.pem ec2-user@${aws_eip.django_app_eip.public_ip}"
  description = "SSH command to connect to the instance"
}