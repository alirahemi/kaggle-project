output "api_url" {
  description = "Cloud Run API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "streamlit_url" {
  description = "Cloud Run Streamlit service URL"
  value       = google_cloud_run_v2_service.streamlit.uri
}

output "database_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "documents_bucket" {
  description = "GCS bucket for encrypted document storage"
  value       = google_storage_bucket.documents.name
}

output "runtime_service_account" {
  description = "Service account email for workloads"
  value       = google_service_account.runtime.email
}

output "artifact_registry" {
  description = "Docker artifact registry path"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_id}"
}
