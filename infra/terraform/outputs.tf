output "region" {
  value       = var.region
  description = "Deployed region (data residency)."
}

output "cluster_name" {
  value       = var.create_gke_cluster ? google_container_cluster.this[0].name : null
  description = "null if create_gke_cluster is false."
}

output "cluster_location" {
  value = var.create_gke_cluster ? google_container_cluster.this[0].location : null
}

output "cluster_endpoint" {
  value       = var.create_gke_cluster ? google_container_cluster.this[0].endpoint : null
  sensitive   = true
  description = "Kubernetes API endpoint (null if create_gke_cluster is false)."
}

output "get_credentials_command" {
  value = var.create_gke_cluster ? "gcloud container clusters get-credentials ${google_container_cluster.this[0].name} --region ${google_container_cluster.this[0].location} --project ${var.project_id}" : null
}

output "vector_embeddings_bucket" {
  value       = google_storage_bucket.vector_embeddings.name
  description = "GCS bucket for embedding batches / Vector Search imports."
}

output "backend_gcp_service_account_email" {
  value       = google_service_account.backend.email
  description = "Bind this to the Kubernetes ServiceAccount via Workload Identity."
}

output "artifact_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
  description = "Container registry URL for docker push (region-docker.pkg.dev/...)."
}
