# Minimal Terraform configuration for Margin App deployment
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Security Group
resource "aws_security_group" "margin_app_sg" {
  name        = "margin-app-sg"
  description = "Security group for Margin Calculator App"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Restrict this to your IP
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Uncomment to allow direct Streamlit access (not recommended for production)
  # ingress {
  #   from_port   = 8501
  #   to_port     = 8501
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "margin-app-sg"
  }
}

# EC2 Instance
resource "aws_instance" "margin_app" {
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2023
  instance_type = "t2.micro"
  key_name      = var.key_pair_name
  
  vpc_security_group_ids = [aws_security_group.margin_app_sg.id]
  
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y docker git
    systemctl start docker
    systemctl enable docker
    usermod -a -G docker ec2-user
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Clone and deploy application
    cd /home/ec2-user
    git clone ${var.repository_url}
    cd Margin-Master-Calculators/Margin\ App/
    docker-compose up -d
  EOF

  tags = {
    Name = "margin-calculator-app"
  }
}

# Elastic IP
resource "aws_eip" "margin_app_eip" {
  instance = aws_instance.margin_app.id
  domain   = "vpc"

  tags = {
    Name = "margin-app-eip"
  }
}

# Outputs
output "instance_ip" {
  value = aws_eip.margin_app_eip.public_ip
}

output "instance_id" {
  value = aws_instance.margin_app.id
}

output "access_url" {
  value = "http://${aws_eip.margin_app_eip.public_ip}"
}