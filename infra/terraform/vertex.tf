# GCS bucket for embedding exports / Vector Search batch imports (text-embedding-004, dim 768).
# Create the Matching Engine index and endpoint after the first successful data run:
#   gsutil -m cp -r gs://.../vector-index/* gs://${bucket}/vector-index/
# Then use gcloud or Console to create/deploy the index, or set var.create_vertex_index = true.

resource "random_id" "bucket_suffix" {
  byte_length = 2
}

resource "google_storage_bucket" "vector_embeddings" {
  # Name stable across applies (random suffix once created). Use labels for environment / developer isolation in console.
  name                        = "${var.project_id}-vertex-emb-${random_id.bucket_suffix.hex}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  labels = merge(
    var.common_labels,
    { environment = var.environment },
    var.developer_id != "" ? { developer_id = var.developer_id } : {}
  )

  depends_on = [google_project_service.storage]
}
