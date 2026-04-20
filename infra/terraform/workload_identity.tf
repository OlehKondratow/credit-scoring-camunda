# Workload Identity: Kubernetes SA -> GCP SA for Vertex AI + GCS (backend).

resource "google_service_account" "backend" {
  account_id   = substr(replace("${var.cluster_name}-backend", "_", "-"), 0, 30)
  display_name = "Millennium credit backend (Vertex AI)"
  project      = var.project_id
}

resource "google_project_iam_member" "backend_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "backend_embeddings_rw" {
  bucket = google_storage_bucket.vector_embeddings.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_service_account_iam_member" "backend_workload_identity" {
  service_account_id = google_service_account.backend.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.k8s_namespace}/${var.backend_ksa_name}]"
}
