# RideSphere

RideSphere is a fictional ride operations and trip management platform. This repository contains the current full-stack foundation for a production-style application, including a FastAPI backend, a React + TypeScript frontend, PostgreSQL connectivity, Alembic migrations, Docker assets, a GitHub Actions CI pipeline, and deployment-oriented repository structure.

This project does not use any real transportation company branding, assets, or proprietary APIs.

## Project Overview

The current repository includes:

- A working FastAPI backend
- A health endpoint at `GET /api/health`
- PostgreSQL database connectivity via SQLAlchemy
- Database session management under `backend/app/database`
- Alembic migration scaffolding
- Initial domain models for users, riders, drivers, vehicles, and driver availability
- Ride Request module with rider-owned ride lifecycle
- Driver availability and nearest-driver matching
- Trip lifecycle management with status history
- Mock payment processing for completed trips
- MongoDB-backed operational event storage for ride and trip lifecycle telemetry
- Redis and Celery-backed background processing for notifications, event handling, and mock payment execution
- Repository, service, and API layering for the initial domain slice
- JWT-based authentication and role-based authorization
- A working React + TypeScript Vite frontend
- Frontend to backend API connectivity
- CORS configuration
- Environment-based configuration
- Dockerfiles for frontend and backend
- A root `docker-compose.yml` with PostgreSQL
- Azure deployment planning documentation
- GitHub Actions CI for backend, frontend, and Docker build validation

The payment flow uses a mock provider only. No real card networks, processors, or sensitive payment data are collected.

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- CSS

### Backend

- Python 3
- FastAPI
- SQLAlchemy
- PostgreSQL
- psycopg
- Pydantic Settings
- Alembic
- FastAPI Security
- JWT
- Pytest
- MongoDB
- PyMongo
- Redis
- Celery

### Infrastructure

- Docker
- Docker Compose
- Kubernetes application manifests for backend, frontend, ingress, and autoscaling
- Microsoft Azure target architecture
- GitHub Actions

## Repository Structure

```text
ridesphere/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_baseline.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements-dev.txt
│   └── requirements.txt
├── docs/
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .env.example
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── infrastructure/
│   ├── docker/
│   └── kubernetes/
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.11+ recommended
- Node.js 20+ recommended
- npm 10+ recommended
- PostgreSQL 16+ recommended
- MongoDB 7+ recommended for operational event storage
- Redis 7+ recommended for background task brokering
- Docker Desktop or Docker Engine with Compose support

## Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
copy .env.example .env
```

Update `backend/.env` so `DATABASE_URL` points to your local PostgreSQL instance with your own credentials, then run:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To run background workers locally, start Redis and then launch Celery in a separate terminal:

```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
```

The backend retries database connectivity during startup. If PostgreSQL is still unavailable after the configured retry window, the application exits instead of serving partially initialized requests.

MongoDB-backed operational event logging is optional outside Docker. If you want it locally, update `backend/.env` with:

```bash
MONGODB_ENABLED=true
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=ridesphere
MONGODB_EVENTS_COLLECTION=operational_events
MONGODB_CONNECT_TIMEOUT_MS=1000
```

If MongoDB is unavailable, business operations still continue. Event persistence is best-effort and failures are logged without blocking the transactional workflow.

If Redis or Celery is unavailable, core transactional writes still complete synchronously. Ride, trip, and payment state changes remain in PostgreSQL, while notifications, event persistence, and mock payment execution fall back safely when needed.

Backend health endpoint:

```text
http://localhost:8000/api/health
```

Example response:

```json
{
  "status": "healthy",
  "application": "RideSphere",
  "database": {
    "status": "healthy",
    "engine": "postgresql",
    "driver": "psycopg",
    "host": "localhost",
    "port": 5432,
    "database": "ridesphere"
  }
}
```

### Initial Domain Endpoints

The backend now exposes initial create/list/get endpoints for:

- `POST /api/users`
- `GET /api/users`
- `GET /api/users/{user_id}`
- `POST /api/riders`
- `GET /api/riders`
- `GET /api/riders/{rider_id}`
- `POST /api/drivers`
- `GET /api/drivers`
- `GET /api/drivers/{driver_id}`
- `POST /api/vehicles`
- `GET /api/vehicles`
- `GET /api/vehicles/{vehicle_id}`
- `POST /api/driver-availabilities`
- `GET /api/driver-availabilities`
- `GET /api/driver-availabilities/{availability_id}`

Password hashes are stored in the database but are never returned by API responses.

### Driver Self-Availability Endpoints

Drivers now have self-service availability endpoints at:

- `PUT /api/v1/drivers/me/availability`
- `GET /api/v1/drivers/me/availability`

Current rules:

- Only authenticated users with the `DRIVER` role can use these endpoints
- Drivers can only modify their own availability
- Allowed statuses for the self-service API are:
  - `OFFLINE`
  - `AVAILABLE`
- Latitude must be between `-90` and `90`
- Longitude must be between `-180` and `180`
- The availability record timestamp is updated on each change

### Ride Request Endpoints

The backend now exposes ride request endpoints at:

- `POST /api/v1/rides`
- `GET /api/v1/rides/{ride_id}`
- `GET /api/v1/rides`
- `POST /api/v1/rides/{ride_id}/cancel`

Current ride request rules:

- Only users with the `RIDER` role can create ride requests
- Riders can only access their own ride requests
- Privileged users can access any ride request:
  - `SUPPORT_AGENT`
  - `PAYMENT_AGENT`
  - `OPERATIONS_MANAGER`
  - `ADMIN`
- New ride requests always start in `REQUESTED` status
- New requests automatically transition to `SEARCHING_DRIVER`
- The nearest eligible `AVAILABLE` driver is selected using the Haversine distance formula
- If a driver is assigned, the ride transitions to `DRIVER_ASSIGNED`
- If no drivers are available, the ride remains in `SEARCHING_DRIVER`

Current supported ride types:

- `STANDARD`
- `XL`
- `PREMIUM`

Current ride request statuses:

- `REQUESTED`
- `SEARCHING_DRIVER`
- `DRIVER_ASSIGNED`
- `CANCELLED`

### Authentication Endpoints

The backend now exposes secure authentication endpoints at:

- `POST /api/v1/auth/register/rider`
- `POST /api/v1/auth/register/driver`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

`POST /api/v1/auth/login` uses the OAuth2 password flow. Submit form-encoded fields where:

- `username` = user email
- `password` = plain-text password

Successful login returns a bearer token:

```json
{
  "access_token": "jwt-token-value",
  "token_type": "bearer"
}
```

`GET /api/v1/auth/me` requires `Authorization: Bearer <token>`.

### Authorization

Reusable role-based authorization dependencies now protect the domain routes. Current examples include:

- `ADMIN` required for `/api/users`
- `ADMIN` or `OPERATIONS_MANAGER` for rider and driver creation
- `ADMIN`, `OPERATIONS_MANAGER`, or `SUPPORT_AGENT` for rider and driver listing
- `ADMIN`, `OPERATIONS_MANAGER`, or `DRIVER` for vehicle and driver-availability creation

### Trip Endpoints

The backend exposes trip lifecycle endpoints at:

- `GET /api/v1/trips/{trip_id}`
- `POST /api/v1/trips/{trip_id}/en-route`
- `POST /api/v1/trips/{trip_id}/arrived`
- `POST /api/v1/trips/{trip_id}/start`
- `POST /api/v1/trips/{trip_id}/complete`

Current trip rules:

- Only the assigned driver can move a trip through driver-controlled states
- Every valid state transition creates a `TripStatusHistory` record
- On trip completion, the driver becomes `AVAILABLE` again
- On trip completion, RideSphere calculates fare and creates a mock payment

### Payment Endpoints

The backend exposes payment endpoints at:

- `GET /api/v1/payments/{payment_id}`
- `GET /api/v1/trips/{trip_id}/payment`
- `POST /api/v1/payments/{payment_id}/refund`

Current payment flow:

- Payments are created only after a trip reaches `TRIP_COMPLETED`
- Fare is calculated from application settings:
  - `PAYMENT_BASE_FARE`
  - `PAYMENT_DISTANCE_RATE_PER_KM`
  - `PAYMENT_DURATION_RATE_PER_MINUTE`
  - `PAYMENT_CURRENCY`
- Payment records are created synchronously in PostgreSQL with initial `PENDING` status
- Mock payment execution is handled through Celery background processing
- Duplicate charges are prevented by a one-payment-per-trip constraint and idempotent payment creation
- Refunds are allowed only for payments in `SUCCESS` state
- Support agents can view payment status, but sensitive payment fields are redacted from their API response

### Background Processing

RideSphere now uses Redis and Celery for non-critical asynchronous work.

Current background task categories:

- Rider notifications
- Driver notifications
- Operational event persistence
- Simulated payment execution

Current design rules:

- PostgreSQL remains the source of truth for transactional state
- Critical ride, trip, and payment record creation stays synchronous
- Background tasks use retries with backoff for appropriate work
- Payment processing is idempotent and does not re-charge successful or refunded payments
- If queue dispatch fails, the application falls back safely instead of losing core transactional updates

### Operational Events

RideSphere now writes best-effort operational events to MongoDB while PostgreSQL remains the source of truth for transactional data.

Current event types:

- `RIDE_REQUESTED`
- `DRIVER_SEARCH_STARTED`
- `DRIVER_ASSIGNED`
- `DRIVER_EN_ROUTE`
- `DRIVER_ARRIVED`
- `TRIP_STARTED`
- `TRIP_COMPLETED`
- `RIDE_CANCELLED`
- `PAYMENT_CREATED`
- `PAYMENT_SUCCESS`
- `PAYMENT_FAILED`
- `REFUND_CREATED`
- `SUPPORT_CASE_CREATED`

Each event document contains:

- `event_id`
- `event_type`
- `ride_id`
- `trip_id`
- `actor_id`
- `timestamp`
- `metadata`

Event metadata is intentionally limited to operationally useful fields and excludes passwords, tokens, raw payment data, and similar sensitive values.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend development server:

```text
http://localhost:5173
```

## Database Migrations

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Show current revision:

```bash
cd backend
alembic current
```

Create a new migration:

```bash
cd backend
alembic revision -m "describe_change"
```

Useful database commands during development:

```bash
cd backend
alembic history
alembic downgrade -1
alembic upgrade head
```

## Running Using Docker

From the repository root:

```bash
copy .env.example .env
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`
- Celery worker: internal service in the compose stack

The compose stack includes PostgreSQL, MongoDB, Redis, the FastAPI backend, the React frontend, and a Celery worker. PostgreSQL remains required for application startup. MongoDB, Redis, and Celery support non-critical operational concerns and background processing.

The root `.env.example` provides the Docker Compose variables required for local startup, including `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`. Copy it to `.env` before running the stack.

## Testing Instructions

### Backend tests

```bash
cd backend
pytest
```

The backend test suite currently covers:

- Database configuration behavior
- Password hashing in the service layer
- Health endpoint behavior
- Integration flows for user, rider, driver, vehicle, and driver availability APIs
- Authentication and authorization flows
- Ride request service validation and ride request API ownership behavior
- Driver self-availability service behavior and API authorization/validation
- Driver matching behavior and concurrency protection
- Trip lifecycle and trip history behavior
- Mock payment creation, access control, redaction, and refund behavior
- Operational event emission and MongoDB-failure fallback behavior
- Background task dispatch, inline fallback behavior, and payment task idempotency

### Alembic migration check

With a configured database connection:

```bash
cd backend
alembic upgrade head
```

For an isolated local migration-chain validation without PostgreSQL, you can use:

```bash
cd backend
set DATABASE_URL=sqlite+pysqlite:///./alembic_check.db
alembic upgrade head
```

### Frontend type check

```bash
cd frontend
npm run typecheck
```

### Frontend production build

```bash
cd frontend
npm run build
```

### Frontend lint and test coverage

```bash
cd frontend
npm run lint
npm run test:coverage
```

### Backend lint and coverage

```bash
cd backend
ruff check app tests
pytest
```

### Docker configuration validation

```bash
docker compose config
docker compose up --build
```

### Kubernetes manifest validation

```bash
kubectl apply --dry-run=client -f infrastructure/kubernetes/configmap.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/secret-example.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/backend-service.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/frontend-deployment.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/frontend-service.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/ingress.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/hpa.yaml
```

If `kubectl` is installed but no cluster API server is available, use the offline YAML parsing approach documented in `infrastructure/kubernetes/README.md`.

## Continuous Integration

GitHub Actions runs on pull requests and on pushes to the `main` branch.

The workflow lives at `.github/workflows/ci.yml` and validates:

- Backend dependency installation, linting with Ruff, pytest execution, and coverage generation
- Frontend dependency installation, ESLint, TypeScript type checking, Vitest coverage, and production build output
- Docker Compose configuration parsing and Docker image builds for the backend and frontend

The workflow does not contain hardcoded credentials. No GitHub secrets are required for the current CI scope.

## Kubernetes

Kubernetes manifests live under `infrastructure/kubernetes/`.

Included resources:

- Backend deployment and service
- Frontend deployment and service
- Shared application ConfigMap
- `secret-example.yaml` for secret shape documentation only
- Ingress routing for `/api` and `/`
- Horizontal Pod Autoscaler for the backend

These manifests intentionally do not deploy PostgreSQL, MongoDB, or Redis as Kubernetes pods. The expected production model is managed external services, which aligns with the planned Azure deployment path.

For local Kubernetes testing:

- Build `ridesphere-backend:local` and `ridesphere-frontend:local`
- Start local PostgreSQL, MongoDB, and Redis with Docker Compose
- Create a real `ridesphere-secrets` Kubernetes secret with connection strings and JWT configuration
- Apply the manifests or use `kubectl port-forward` if an ingress controller is not available

See [infrastructure/kubernetes/README.md](/E:/Git%20Hub%20Repo/infrastructure/kubernetes/README.md) for the full local testing flow.

## Azure Deployment Planning

RideSphere is prepared for a managed Azure production architecture based on:

- Azure Kubernetes Service for application containers
- Azure Container Registry for image storage
- Azure Database for PostgreSQL for transactional data
- Azure Cosmos DB for operational event storage
- Azure Cache for Redis for Redis and Celery infrastructure
- Azure Key Vault for secrets
- Azure Blob Storage for optional future file storage
- Application Insights and Azure Monitor for observability

The Azure preparation work does not deploy infrastructure automatically and does not break local Docker development. Existing local connection-string settings remain valid, while optional Azure-oriented settings are available for:

- `AZURE_KEY_VAULT_URL`
- `APPLICATIONINSIGHTS_CONNECTION_STRING`
- `AZURE_BLOB_STORAGE_ACCOUNT_URL`
- `AZURE_BLOB_STORAGE_CONTAINER`

See [docs/azure-deployment.md](/E:/Git%20Hub%20Repo/docs/azure-deployment.md) for architecture, environment variables, deployment flow, secret management, scaling, and monitoring guidance.

## Environment Variables

Example environment files are included at:

- `.env.example`
- `backend/.env.example`
- `frontend/.env.example`

Do not commit real secrets. Use local `.env` files, shell environment variables, or deployment-specific secret management.

Authentication-related backend settings include:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

Payment-related backend settings include:

- `PAYMENT_BASE_FARE`
- `PAYMENT_DISTANCE_RATE_PER_KM`
- `PAYMENT_DURATION_RATE_PER_MINUTE`
- `PAYMENT_CURRENCY`

MongoDB-related backend settings include:

- `MONGODB_ENABLED`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `MONGODB_EVENTS_COLLECTION`
- `MONGODB_CONNECT_TIMEOUT_MS`

Redis and Celery-related backend settings include:

- `REDIS_URL`
- `CELERY_ENABLED`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_TASK_ALWAYS_EAGER`
- `CELERY_TASK_EAGER_PROPAGATES`
- `CELERY_WORKER_LOG_LEVEL`
- `CELERY_DEFAULT_QUEUE`
- `CELERY_TASK_MAX_RETRIES`
