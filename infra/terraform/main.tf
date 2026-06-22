terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }

  backend "gcs" {
    bucket = "CHANGE_ME-terraform-state"
    prefix = "german-bureaucracy-agent"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.artifact_repo_id
  description   = "Container images for German Bureaucracy AI Agent"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "documents" {
  name                        = "${var.project_id}-bureaucracy-documents"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = var.environment != "production"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.document_retention_days
    }
    action {
      type = "Delete"
    }
  }
}
