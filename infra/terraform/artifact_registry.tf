resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = "${replace(var.cluster_name, "_", "-")}-docker"
  description   = "credit-backend, credit-worker, credit-ui images"
  format        = "DOCKER"

  labels = merge(
    var.common_labels,
    { environment = var.environment },
    var.developer_id != "" ? { developer_id = var.developer_id } : {}
  )

  depends_on = [google_project_service.artifactregistry]
}
