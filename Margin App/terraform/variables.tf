variable "key_pair_name" {
  description = "Name of the AWS Key Pair for EC2 access"
  type        = string
}

variable "repository_url" {
  description = "Git repository URL for the application"
  type        = string
  default     = "https://github.com/your-repo/Margin-Master-Calculators.git"
}