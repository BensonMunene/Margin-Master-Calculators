variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
  default     = "ami-0c02fb55956c7d316" # Amazon Linux 2023 in us-east-1
}

variable "key_pair_name" {
  description = "Name of the EC2 key pair"
  type        = string
}

variable "ssh_allowed_ips" {
  description = "List of IP addresses allowed to SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Update this to restrict SSH access
}

variable "http_allowed_ips" {
  description = "List of IP addresses allowed to access HTTP"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Update this to restrict HTTP access
}

variable "https_allowed_ips" {
  description = "List of IP addresses allowed to access HTTPS"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Update this to restrict HTTPS access
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms (optional)"
  type        = string
  default     = ""
}

variable "repository_url" {
  description = "Git repository URL for the application"
  type        = string
  default     = ""
}