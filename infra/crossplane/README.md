# Crossplane (GCP)

Crossplane разворачивает **провайдер** в Kubernetes и создаёт ресурсы GCP через **CRD** (не Terraform state в файле).

## Установка (общая схема)

1. Установить [Crossplane](https://docs.crossplane.io/latest/software/install/) в целевой GKE.
2. Установить провайдер GCP (часто **Upbound provider-gcp** или семейство провайдеров).
3. Создать `ProviderConfig` с учётными данными (Workload Identity или ключ — по политике безопасности).

Пакеты и версии меняются; актуальные команды: [Upbound GCP Provider](https://marketplace.upbound.io/providers/upbound/provider-family-gcp).

## Файлы в этом каталоге

- `providerconfig-gcp.yaml.example` — шаблон привязки к GCP (подставьте проект и секрет).

Managed resources (Bucket, ArtifactRegistry и т.д.) добавляйте по документации выбранного провайдера — API отличается от Terraform и от Config Connector.

**Не смешивайте** Crossplane и Config Connector в одном кластере для одних и тех же ресурсов.
