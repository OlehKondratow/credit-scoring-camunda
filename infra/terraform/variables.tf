variable "project_id" {
  description = "GCP project ID."
  type        = string
}

# Isolation: label resources and choose logical env (dev / staging / prod). CI should use separate state per env.
variable "environment" {
  description = "Logical environment name for labels and operations (e.g. dev, staging, prod)."
  type        = string
  default     = "dev"
}

# Optional: set to short id (e.g. github login) when using a per-developer Kubernetes namespace.
variable "developer_id" {
  description = "Optional identifier for per-developer sandbox (labels only; pair with k8s_namespace like millennium-credit-dev-NAME)."
  type        = string
  default     = ""
}

variable "common_labels" {
  description = "Extra GCP labels merged onto supported resources (team, cost_center, etc.)."
  type        = map(string)
  default     = {}
}

# Data residency: Warsaw region (EU).
variable "region" {
  description = "GCP region for GKE, GCS, and Vertex AI (hardcoded default for Bank Millennium workloads)."
  type        = string
  default     = "europe-central2"
}

variable "cluster_name" {
  description = "GKE Standard cluster name (not Autopilot — Camunda/Zeebe compatible)."
  type        = string
  default     = "millennium-credit-gke"
}

variable "node_pool_name" {
  type    = string
  default = "primary"
}

variable "min_node_count" {
  type    = number
  default = 2
}

variable "max_node_count" {
  type    = number
  default = 6
}

variable "machine_type" {
  type    = string
  default = "e2-standard-4"
}

variable "disk_size_gb" {
  type    = number
  default = 40
}

variable "preemptible" {
  type    = bool
  default = false
}

variable "release_channel" {
  type    = string
  default = "REGULAR"

  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "release_channel must be RAPID, REGULAR, or STABLE."
  }
}

variable "deletion_protection" {
  type    = bool
  default = false
}

# When false, Terraform does NOT create a GKE cluster (keeps costs down if you already use e.g. camunda-stable elsewhere).
variable "create_gke_cluster" {
  description = "If true, create a new Standard GKE cluster in var.region. If false, only APIs, GCS, Artifact Registry, and backend Workload Identity SA are created."
  type        = bool
  default     = true
}

variable "k8s_namespace" {
  description = "Kubernetes namespace for workload identity binding (must match manifests)."
  type        = string
  default     = "millennium-credit"
}

variable "backend_ksa_name" {
  description = "Kubernetes ServiceAccount name for backend (Workload Identity)."
  type        = string
  default     = "backend-sa"
}
