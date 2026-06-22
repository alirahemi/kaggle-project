variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP region (EU recommended)"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

variable "app_name" {
  description = "Application name prefix for resources"
  type        = string
  default     = "bureaucracy-agent"
}

variable "artifact_repo_id" {
  description = "Artifact Registry repository ID"
  type        = string
  default     = "bureaucracy-agent"
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}

variable "db_name" {
  type    = string
  default = "bureaucracy"
}

variable "db_user" {
  type    = string
  default = "bureaucracy"
}

variable "db_password" {
  description = "Cloud SQL password — use Secret Manager in production"
  type        = string
  sensitive   = true
}

variable "db_tier" {
  type    = string
  default = "db-custom-2-7680"
}

variable "db_disk_size_gb" {
  type    = number
  default = 20
}

variable "vpc_network_id" {
  description = "VPC self link for private Cloud SQL"
  type        = string
  default     = ""
}

variable "document_retention_days" {
  type    = number
  default = 30
}

variable "cloud_run_min_instances" {
  type    = number
  default = 0
}

variable "cloud_run_max_instances" {
  type    = number
  default = 5
}

variable "allow_unauthenticated" {
  description = "Allow public access to Cloud Run services (demo only)"
  type        = bool
  default     = false
}

variable "jwt_secret_key" {
  type      = string
  sensitive = true
}
