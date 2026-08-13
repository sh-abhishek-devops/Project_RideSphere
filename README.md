# RideSphere

RideSphere is a fictional ride operations and trip management platform. This repository contains a FastAPI backend, a React + TypeScript frontend, PostgreSQL persistence, Alembic migrations, Docker assets, CI automation, and deployment-oriented infrastructure docs.

This project does not use any real transportation company branding, assets, or proprietary APIs.

## Functional Use Cases

RideSphere currently supports these main business flows:

- Rider registration and login
- Driver registration and login
- Rider ride request creation with pickup, destination, ride type, estimated distance, and estimated duration
- Driver availability updates and assignment readiness
- Automatic driver matching for eligible nearby available drivers
- Driver ride-offer acceptance
- Rider current-ride tracking across request, search, assignment, pickup, trip start, and completion
- Rider trip-start PIN sharing, where the rider receives a 6-digit PIN and the driver must enter the same PIN before the trip can start
- Driver trip progression through `DRIVER_ASSIGNED`, `DRIVER_EN_ROUTE`, `DRIVER_ARRIVED`, `TRIP_STARTED`, and `TRIP_COMPLETED`
- Mock fare and payment creation after trip completion
- Operations dashboard reporting for operations and admin roles
- Support-case creation, assignment, investigation, updating, and resolution
- Operational event logging and background task processing for non-critical asynchronous workflows

## Functional Roles

- `RIDER`: can self-register, log in, request rides, track rides, view the trip-start PIN, and cancel eligible rides
- `DRIVER`: can self-register, log in, update availability, accept ride offers, verify the rider PIN, and progress assigned trips
- `SUPPORT_AGENT`: can log in with a pre-created account and investigate rides, payments, and support cases
- `PAYMENT_AGENT`: can log in with a pre-created account, review payments, issue refunds, and work support investigations
- `OPERATIONS_MANAGER`: can log in with a pre-created account and access operations dashboards and support workflows
- `ADMIN`: can log in with a pre-created account and has full platform access across the current modules

Only `RIDER` and `DRIVER` currently have public self-registration flows.

`SUPPORT_AGENT`, `PAYMENT_AGENT`, `OPERATIONS_MANAGER`, and `ADMIN` accounts must already exist before login. In the current system, those accounts are expected to be created either:

- by an existing admin using the protected user-management APIs
- by a manual database insert or a seed script for initial environment setup

## Project Overview

The current repository includes:

- A working FastAPI backend
- A health endpoint at `GET /api/health`
- PostgreSQL connectivity via SQLAlchemy
- Alembic migration history through support cases, payments, trips, ride requests, and rider PIN verification
- JWT-based authentication and role-based authorization
- Driver availability and nearest-driver matching
- Ride request creation, assignment, cancellation, and rider ownership checks
- Driver ride offers and acceptance flow
- Trip lifecycle management with status history
- Rider-to-driver trip-start PIN verification before trip start
- Mock payment processing for completed trips
- MongoDB-backed operational event storage
- Redis and Celery-backed background processing
- Support-case workflows and investigation endpoints
- Operations dashboard reporting
- A React + TypeScript Vite frontend with rider, driver, support, and operations screens
- Dockerfiles for frontend and backend
- A root `docker-compose.yml` for local multi-service startup
- Kubernetes manifests and Azure deployment planning documentation
- GitHub Actions CI for backend, frontend, and Docker validation

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
- JWT
- Pytest
- MongoDB
- PyMongo
- Redis
- Celery

### Infrastructure

- Docker
- Docker Compose
- Kubernetes manifests for backend, frontend, ingress, and autoscaling
- Microsoft Azure target architecture documentation
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
│   │   │   ├── 0001_baseline.py
│   │   │   ├── 0002_initial_domain_models.py
│   │   │   ├── 0003_ride_request_module.py
│   │   │   ├── 0004_trip_domain.py
│   │   │   ├── 0005_payment_domain.py
│   │   │   ├── 0006_support_cases.py
│   │   │   └── 0007_trip_start_pin.py
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
│   │   ├── tasks/
│   │   └── main.py
│   ├── tests/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── pytest.ini
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   └── ruff.toml
├── docs/
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── infrastructure/
│   ├── docker/
│   └── kubernetes/
├── .env.example
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
```

Configure backend environment values so `DATABASE_URL` points to your local PostgreSQL instance, then run:

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To run background workers locally, start Redis and then launch Celery in a separate terminal:

```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
```

MongoDB-backed operational event logging is optional outside Docker. Redis and Celery support non-critical asynchronous work and safe fallback behavior.

Backend health endpoint:

```text
http://localhost:8000/api/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend development server:

```text
http://localhost:5173
```

The current frontend includes:

- Rider registration, login, dashboard, ride request, current ride, and ride history screens
- Driver registration, login, dashboard, availability, current trip, and trip history screens
- Driver trip-start PIN verification modal
- Support dashboard, case details, and investigation screens
- Operations dashboard screens

## Current Backend Endpoints

### Authentication

- `POST /api/v1/auth/register/rider`
- `POST /api/v1/auth/register/driver`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

`POST /api/v1/auth/login` uses the OAuth2 password flow with form fields:

- `username`: user email
- `password`: plain-text password

### Driver Self-Availability

- `PUT /api/v1/drivers/me/availability`
- `GET /api/v1/drivers/me/availability`

Rules:

- Only authenticated drivers can use these endpoints
- Allowed self-service statuses are `OFFLINE` and `AVAILABLE`
- Latitude must be between `-90` and `90`
- Longitude must be between `-180` and `180`

### Ride Requests

- `POST /api/v1/rides`
- `GET /api/v1/rides/{ride_id}`
- `GET /api/v1/rides`
- `POST /api/v1/rides/{ride_id}/cancel`

Rules:

- Only riders can create ride requests
- Riders can access only their own rides
- Privileged access roles are `SUPPORT_AGENT`, `PAYMENT_AGENT`, `OPERATIONS_MANAGER`, and `ADMIN`
- New ride requests start in `REQUESTED`
- Requests transition to `SEARCHING_DRIVER`
- The nearest eligible `AVAILABLE` driver is selected
- Assigned rides transition to `DRIVER_ASSIGNED`
- If no drivers are available, the ride remains in `SEARCHING_DRIVER`

Supported ride types:

- `STANDARD`
- `XL`
- `PREMIUM`

### Driver Ride Offers

- `GET /api/v1/drivers/me/ride-offers`
- `POST /api/v1/drivers/me/ride-offers/{ride_id}/accept`

Rules:

- Only authenticated drivers can access these endpoints
- Accepting an offer creates or reuses the linked trip record
- The linked trip stores the rider trip-start PIN used later at trip start

### Trips

- `GET /api/v1/trips/{trip_id}`
- `GET /api/v1/drivers/me/trips`
- `POST /api/v1/trips/{trip_id}/en-route`
- `POST /api/v1/trips/{trip_id}/arrived`
- `POST /api/v1/trips/{trip_id}/start`
- `POST /api/v1/trips/{trip_id}/complete`

Rules:

- Only the assigned driver can move a trip through driver-controlled states
- Starting a trip requires the driver to submit the rider's matching 6-digit PIN
- Rider-facing ride and trip responses include the PIN when applicable
- Driver-facing trip responses do not expose the stored PIN value
- Every valid state transition creates a `TripStatusHistory` record
- On trip completion, the driver becomes `AVAILABLE` again
- On trip completion, RideSphere calculates fare and creates a mock payment

### Payments

- `GET /api/v1/payments/{payment_id}`
- `GET /api/v1/trips/{trip_id}/payment`
- `POST /api/v1/payments/{payment_id}/refund`

Rules:

- Payments are created only after `TRIP_COMPLETED`
- Payment creation is synchronous in PostgreSQL with background mock execution
- Refunds are allowed only for payments in `SUCCESS`
- Duplicate charges are prevented by trip-level uniqueness and idempotency

### Operations

- `GET /api/v1/operations/dashboard`

Rules:

- Only `OPERATIONS_MANAGER` and `ADMIN` can access the dashboard
- Optional `date_from` and `date_to` query parameters can scope the metrics window

### Support

- `GET /api/v1/support/agents`
- `POST /api/v1/support/cases`
- `GET /api/v1/support/cases`
- `GET /api/v1/support/cases/{case_id}`
- `PATCH /api/v1/support/cases/{case_id}`
- `POST /api/v1/support/cases/{case_id}/resolve`
- `GET /api/v1/support/cases/{case_id}/investigation`

Rules:

- Access is limited to `SUPPORT_AGENT`, `PAYMENT_AGENT`, `OPERATIONS_MANAGER`, and `ADMIN`
- Support cases can be linked to rides and trips
- Investigation responses can include rider, driver, vehicle, trip, and payment context

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

The compose stack includes PostgreSQL, MongoDB, Redis, the FastAPI backend, the React frontend, and a Celery worker.

## Testing Instructions

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

### Docker

```bash
docker compose config
docker compose up --build
```

## Continuous Integration

GitHub Actions runs on pull requests and on pushes to the `main` branch.

The workflow validates:

- Backend dependency installation, linting, and pytest execution
- Frontend dependency installation, ESLint, TypeScript checks, Vitest, and production build output
- Docker Compose parsing and backend/frontend image builds

## Kubernetes

Kubernetes manifests live under `infrastructure/kubernetes/`.

Included resources:

- Backend deployment and service
- Frontend deployment and service
- Shared application ConfigMap
- `secret-example.yaml` for secret-shape documentation
- Ingress routing for `/api` and `/`
- Horizontal Pod Autoscaler for the backend

See [infrastructure/kubernetes/README.md](/E:/Git%20Hub%20Repo/infrastructure/kubernetes/README.md) for local testing details.

## Azure Deployment Planning

See [docs/azure-deployment.md](/E:/Git%20Hub%20Repo/docs/azure-deployment.md) for Azure architecture, environment variables, deployment flow, secret management, scaling, and monitoring guidance.

## Environment Variables

Example environment files are included at:

- `.env.example`

Important backend settings include:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `PAYMENT_BASE_FARE`
- `PAYMENT_DISTANCE_RATE_PER_KM`
- `PAYMENT_DURATION_RATE_PER_MINUTE`
- `PAYMENT_CURRENCY`
- `MONGODB_ENABLED`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `MONGODB_EVENTS_COLLECTION`
- `REDIS_URL`
- `CELERY_ENABLED`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Do not commit real secrets. Use local environment files, shell variables, or deployment-specific secret management.
