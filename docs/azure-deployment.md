# RideSphere Azure Deployment Guide

## Objective

This document describes the target Microsoft Azure production architecture for RideSphere without automating deployment yet.

The current guidance assumes:

- application containers run on Azure Kubernetes Service
- container images are stored in Azure Container Registry
- relational data uses Azure Database for PostgreSQL
- operational event storage uses Azure Cosmos DB with the MongoDB-compatible API
- caching and Celery broker/result traffic use Azure Cache for Redis
- secrets are managed through Azure Key Vault
- optional file or artifact storage uses Azure Blob Storage
- application telemetry uses Application Insights
- infrastructure monitoring and alerting use Azure Monitor

## Target Architecture

### Application tier

- `frontend` container runs in AKS behind an ingress controller
- `backend` container runs in AKS with multiple replicas
- a future `celery-worker` container can run in AKS as a separate deployment when background scale needs to be managed independently

### Managed data tier

- Azure Database for PostgreSQL stores transactional application data
- Azure Cosmos DB stores non-blocking operational event records
- Azure Cache for Redis backs Redis access and Celery broker/result infrastructure

### Security and configuration tier

- Azure Key Vault stores application secrets
- AKS workloads should receive secrets through a secure delivery mechanism such as the Key Vault provider for the Secrets Store CSI driver or a controlled secret-sync step

### Observability tier

- Application Insights collects request, dependency, trace, and exception telemetry
- Azure Monitor collects cluster and infrastructure metrics, log queries, dashboards, and alert rules

## Azure Resources

Recommended resource inventory:

- 1 Azure Kubernetes Service cluster
- 1 Azure Container Registry instance
- 1 Azure Database for PostgreSQL flexible server
- 1 Azure Cosmos DB account configured for MongoDB-compatible connectivity
- 1 Azure Cache for Redis instance
- 1 Azure Key Vault
- 1 Application Insights resource
- 1 Log Analytics workspace for Azure Monitor
- 1 Storage account with Blob Storage enabled if application file storage is needed later

Optional supporting resources:

- public IP and DNS records for ingress
- Azure Managed Identity for AKS workloads
- Azure Monitor alerts and dashboards
- Azure Front Door or Application Gateway in front of ingress if edge controls are required later

## How RideSphere Maps to Azure

Existing application settings already support the core managed services:

- `DATABASE_URL` maps to Azure Database for PostgreSQL
- `MONGODB_URL`, `MONGODB_DATABASE`, and `MONGODB_EVENTS_COLLECTION` map to Azure Cosmos DB
- `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` map to Azure Cache for Redis
- `JWT_SECRET_KEY` should come from Azure Key Vault

Additive Azure-oriented settings are now available in backend configuration:

- `AZURE_KEY_VAULT_URL`
- `APPLICATIONINSIGHTS_CONNECTION_STRING`
- `AZURE_BLOB_STORAGE_ACCOUNT_URL`
- `AZURE_BLOB_STORAGE_CONTAINER`

These settings are optional and do not change local Docker behavior when left unset.

## Environment Variables

### Core application

- `APP_NAME`
- `APP_ENV`
- `API_PREFIX`
- `BACKEND_HOST`
- `BACKEND_PORT`
- `FRONTEND_ORIGINS`

### Database and messaging

- `DATABASE_URL`
- `DATABASE_RETRY_ATTEMPTS`
- `DATABASE_RETRY_DELAY_SECONDS`
- `MONGODB_ENABLED`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `MONGODB_EVENTS_COLLECTION`
- `MONGODB_CONNECT_TIMEOUT_MS`
- `REDIS_URL`
- `CELERY_ENABLED`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_TASK_ALWAYS_EAGER`
- `CELERY_TASK_EAGER_PROPAGATES`
- `CELERY_WORKER_LOG_LEVEL`
- `CELERY_DEFAULT_QUEUE`
- `CELERY_TASK_MAX_RETRIES`

### Security

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

### Payment configuration

- `PAYMENT_BASE_FARE`
- `PAYMENT_DISTANCE_RATE_PER_KM`
- `PAYMENT_DURATION_RATE_PER_MINUTE`
- `PAYMENT_CURRENCY`

### Azure-specific optional settings

- `AZURE_KEY_VAULT_URL`
- `APPLICATIONINSIGHTS_CONNECTION_STRING`
- `AZURE_BLOB_STORAGE_ACCOUNT_URL`
- `AZURE_BLOB_STORAGE_CONTAINER`

## Secret Management

Do not place production secrets in Git, Dockerfiles, or committed Kubernetes manifests.

Recommended Azure secret flow:

1. Store secret values in Azure Key Vault.
2. Grant AKS workload access through Managed Identity.
3. Project secrets into pods using the Secrets Store CSI driver or synchronize them into Kubernetes secrets through an approved process.
4. Reference those runtime-provided values through environment variables.

Secrets that belong in Key Vault:

- PostgreSQL password or full `DATABASE_URL`
- Cosmos DB connection string or `MONGODB_URL`
- Redis access key or Redis URLs
- `JWT_SECRET_KEY`
- any future API keys or storage credentials
- Application Insights connection string if you choose not to expose it as plain configuration

## Deployment Flow

Recommended manual release flow:

1. Run local and CI validation.
2. Build `backend` and `frontend` images.
3. Tag images with an immutable version such as a Git SHA.
4. Push images to Azure Container Registry.
5. Update AKS manifests or Helm values with the new ACR image references.
6. Ensure Key Vault-backed secrets are present for the target environment.
7. Apply manifests to AKS.
8. Verify backend health, frontend availability, database connectivity, and telemetry.

Suggested image naming:

- `acr-name.azurecr.io/ridesphere/backend:<git-sha>`
- `acr-name.azurecr.io/ridesphere/frontend:<git-sha>`

## Scaling

### Backend

- run multiple replicas in AKS
- use Horizontal Pod Autoscaler based on CPU and memory
- keep PostgreSQL and Redis connections sized for peak replica count

### Frontend

- scale horizontally with multiple replicas behind ingress
- keep frontend stateless

### Background work

- separate Celery workers from API pods when production load warrants it
- scale workers independently based on queue depth or CPU

## Monitoring

### Application Insights

Use Application Insights for:

- request tracing
- dependency telemetry for PostgreSQL, Cosmos DB, and Redis calls
- exception monitoring
- application-side latency tracking

### Azure Monitor

Use Azure Monitor for:

- AKS node and pod health
- CPU and memory saturation
- ingress availability
- cluster events
- alert routing

Recommended initial alerts:

- backend error rate above threshold
- backend p95 latency above threshold
- pod restart spikes
- HPA max replica saturation
- PostgreSQL connectivity failures
- Redis connectivity failures
- Cosmos DB connectivity failures

## Local Development Compatibility

The Azure preparation changes are additive only.

Local Docker development remains unchanged:

- Docker Compose can continue using local PostgreSQL, MongoDB, and Redis containers
- existing connection strings and feature flags still work
- Azure-specific settings may remain empty locally

## Next Step Candidates

When you are ready to automate deployment later, the next implementation steps would typically be:

- ACR build and push workflow
- AKS environment overlays or Helm chart packaging
- Key Vault to AKS secret delivery configuration
- Application Insights SDK or OpenTelemetry integration in the backend
- Azure-specific CI/CD workflows
