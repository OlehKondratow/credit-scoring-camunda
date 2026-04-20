# Google Cloud Config Connector (KCC)

Примеры **Config Connector** — управление ресурсами GCP через **Custom Resources** в Kubernetes.

## Требования

- Установленный [Config Connector](https://cloud.google.com/config-connector/docs/overview) в кластере GKE.
- Namespace с аннотацией проекта или `cnrm.cloud.google.com/project-id` (см. документацию KCC).

## Применение

```bash
kubectl apply -f storage-bucket.yaml
kubectl apply -f artifact-registry-repository.yaml
```

Не применяйте параллельно с Terraform/Pulumi на **конфликтующие имена** ресурсов в одном GCP-проекте.
