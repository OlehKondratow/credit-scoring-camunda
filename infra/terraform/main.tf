# Standard GKE (not Autopilot) for Camunda Platform / Zeebe compatibility.

locals {
  env_labels = merge(
    var.common_labels,
    { environment = var.environment },
    var.developer_id != "" ? { developer_id = var.developer_id } : {}
  )
}

resource "google_project_service" "container" {
  project = var.project_id
  service = "container.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "aiplatform" {
  project = var.project_id
  service = "aiplatform.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"

  disable_on_destroy = false
}

resource "google_container_cluster" "this" {
  count = var.create_gke_cluster ? 1 : 0

  name     = var.cluster_name
  location = var.region

  deletion_protection = var.deletion_protection

  remove_default_node_pool = true
  initial_node_count       = 1

  release_channel {
    channel = var.release_channel
  }

  network    = "default"
  subnetwork = "default"

  ip_allocation_policy {}

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  resource_labels = local.env_labels

  depends_on = [
    google_project_service.container,
  ]
}

resource "google_container_node_pool" "primary" {
  count = var.create_gke_cluster ? 1 : 0

  name     = var.node_pool_name
  location = var.region
  cluster  = google_container_cluster.this[0].name

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible     = var.preemptible
    machine_type    = var.machine_type
    disk_size_gb    = var.disk_size_gb
    disk_type       = "pd-balanced"
    service_account = google_service_account.gke_nodes[0].email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  depends_on = [google_container_cluster.this]
}

resource "google_service_account" "gke_nodes" {
  count = var.create_gke_cluster ? 1 : 0

  account_id   = substr(replace("${var.cluster_name}-nodes", "_", "-"), 0, 30)
  display_name = "GKE nodes for ${var.cluster_name}"
  project      = var.project_id
}

resource "google_project_iam_member" "gke_nodes_log_writer" {
  count = var.create_gke_cluster ? 1 : 0

  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes[0].email}"
}

resource "google_project_iam_member" "gke_nodes_metric_writer" {
  count = var.create_gke_cluster ? 1 : 0

  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes[0].email}"
}
