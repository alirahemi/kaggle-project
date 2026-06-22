resource "google_cloud_run_v2_service" "api" {
  name     = "${var.app_name}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_id}/api:${var.image_tag}"

      ports {
        container_port = 8000
      }

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://${var.db_user}:${var.db_password}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "USE_VERTEX_AI"
        value = "true"
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.main,
  ]
}

resource "google_cloud_run_v2_service" "streamlit" {
  name     = "${var.app_name}-streamlit"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_id}/streamlit:${var.image_tag}"

      ports {
        container_port = 8501
      }

      env {
        name  = "STREAMLIT_API_BASE_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }

  depends_on = [google_cloud_run_v2_service.api]
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  count = var.allow_unauthenticated ? 1 : 0

  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "streamlit_public" {
  count = var.allow_unauthenticated ? 1 : 0

  name     = google_cloud_run_v2_service.streamlit.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
