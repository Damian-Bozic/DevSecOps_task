# DevSecOps_task

## Overview

This project implements a simple CRUD application together with a DevSecOps environment.

The solution covers:

- REST API development
- In-memory data storage
- Docker containerization
- Centralized logging and visualization
- Automated testing and linting
- Dependency security scanning
- Container vulnerability scanning
- CI/CD with GitHub Actions
- Quality gates that prevent delivery when defined checks fail

---

# 1. Application

## Technology

The application is written in **Python** using **FastAPI**.

FastAPI was selected because it provides a lightweight way to build REST APIs, includes automatic request validation through Pydantic, and automatically provides OpenAPI/Swagger documentation.

## Resource

The application manages a single resource: **Product**.

Each product contains:

- `id`
- `name`
- `category`
- `price`

## In-memory data

The application uses an in-memory Python dictionary as its data store.

At startup, **2000 products are generated and loaded into memory**.

## REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/products` | List products |
| GET | `/products/{product_id}` | Get a specific product |
| POST | `/products` | Create a product |
| PUT | `/products/{product_id}` | Update a product |
| DELETE | `/products/{product_id}` | Delete a product |
| GET | `/health` | Application health check |

FastAPI's automatically generated documentation is available at:

```text
http://localhost:8000/docs
```

## Input validation

Pydantic models validate incoming data.

Examples include:

- product names must contain 1–100 characters
- categories must contain 1–50 characters
- prices must be greater than zero
- product IDs must be integers
- listing limits must be between 1 and 100
- offsets cannot be negative

Invalid requests are rejected by the API.

## Handling a large number of records

The list endpoint implements pagination using `limit` and `offset`.

Example:

```text
GET /products?limit=50&offset=0
```

The default page size is 50 and the maximum page size is 100. This prevents a client from requesting all 2000 records in a single response and provides a meaningful mechanism for handling the larger dataset.

## Logging

The application uses Python logging and produces diagnostic information such as:

- application startup
- number of products loaded
- product creation
- product updates
- product deletion
- attempts to access products that do not exist

Uvicorn also produces HTTP request and application lifecycle logs.

These logs are subsequently collected by the logging stack described below.

---

# 2. Containerization

## Dockerfile

The application is packaged using Docker with a Python 3.12 slim base image.

The Dockerfile:

- installs the application from `pyproject.toml`
- copies the application source
- exposes port `8000`
- starts the application using Uvicorn
- runs the application using a configurable non-root user

The final runtime image does not contain the application's development dependencies.

## Non-root execution

The application container does not run as root.

The application user and group IDs are configurable through Docker build arguments.

Example `.env` configuration:

```env
APP_UID=1000
APP_GID=1000
```

An `.env.example` file is included to document the required configuration.

The real `.env` file is excluded from Git tracking.

The application container was verified to run as:

```text
uid=1000(appuser) gid=1000(appgroup)
```

rather than root.

## Docker Compose

The complete environment is defined in:

```text
docker-compose.yml
```

It runs four services:

- FastAPI application
- Loki
- Promtail
- Grafana

The entire environment can be started with one command.

---

# 3. Logging and visualization

## Loki

**Grafana Loki** is used as the centralized log storage system.

Loki receives logs from Promtail and makes them available for querying.

Loki is kept on the Docker Compose internal network rather than being exposed directly to the host. This reduces unnecessary network exposure while allowing Grafana and Promtail to communicate with Loki.

## Promtail

Promtail collects Docker container logs and sends them to Loki.

It uses Docker service discovery through:

```text
/var/run/docker.sock
```

The Docker socket is mounted read-only.

Container names and log streams are included as labels so that logs can be identified and filtered.

**Security trade-off:** Promtail currently runs with the default root user from its image because Docker service discovery requires access to the Docker daemon socket. The socket is mounted read-only. This is an intentional trade-off and should be considered when moving the stack to a production environment.

## Grafana

**Grafana** provides the browser-based interface for querying and visualizing the collected logs.

The Loki data source is provisioned automatically through the repository configuration.

Grafana is available at:

```text
http://localhost:3000
```

## Network exposure

Only the services that need to be reached from the host are exposed:

- FastAPI: `8000`
- Grafana: `3000`

Loki is available internally as `http://loki:3100` but is not published to the host. Promtail does not expose a host port.

---

# 4. CI/CD Pipeline

GitHub Actions is used to implement CI/CD.

The workflows are stored in:

```text
.github/workflows/
```

The pipeline runs on pushes to `main` and pull requests targeting `main` for CI. The CD workflow publishes the resulting Docker image when changes are pushed to `main`.

## CI stages

### Code checkout

The repository is checked out using GitHub Actions.

### Python environment

Python 3.12 is installed using `actions/setup-python`.

### Dependency installation

The application and development dependencies are installed from `pyproject.toml`.

### Ruff

Ruff checks the project for code-quality and linting issues:

```text
ruff check .
```

### Pytest

The automated test suite is executed using:

```text
pytest
```

The project's pytest configuration also requires a minimum **80% code coverage**.

The current test suite passes with 100% coverage.

### pip-audit

Python dependencies are checked for known vulnerabilities using:

```text
pip-audit
```

The local dependency audit reported:

```text
No known vulnerabilities found
```

The local application package itself is not published to PyPI, so pip-audit reports that the `devsecops-crud` package cannot be independently audited through PyPI. This is expected for the local application package.

### Docker image build and Trivy

The CI pipeline builds the Docker image and scans the resulting image using Trivy.

The security gate is configured to fail when fixed **HIGH** or **CRITICAL** vulnerabilities are detected.

During development, Trivy identified vulnerabilities in packages included in an earlier image. The dependency/image configuration was subsequently corrected and the image was rebuilt and rescanned. The final GitHub Actions container security scan passed.

---

# 5. Quality Gate

The pipeline contains multiple quality and security checks. A change cannot successfully pass the pipeline if the defined checks fail.

The current gates are:

- Ruff linting
- automated pytest tests
- minimum 80% test coverage
- `pip-audit` dependency scanning
- Docker image build
- Trivy container vulnerability scanning
- HIGH/CRITICAL vulnerability failure criteria for Trivy

This provides automated verification of:

- code quality
- functional correctness
- test coverage
- dependency security
- container security

The final CI and CD workflows both completed successfully in GitHub Actions.

---

# 6. Container and dependency security

Several security considerations were addressed during development.

## Non-root application

The application container runs using a dedicated non-root user rather than root.

## Dependency minimization

The runtime Docker image contains only the dependencies required to run the application. Development dependencies are not installed into the runtime image.

This was important when Trivy identified vulnerabilities in packages that were present in an earlier image. The dependency tree was investigated and unnecessary packages were removed from the runtime environment.

## Vulnerability scanning

Both Python dependencies and the final Docker image are scanned automatically.

```text
Python dependencies
        |
        v
    pip-audit
```

and:

```text
Docker image
        |
        v
      Trivy
```

## `.dockerignore`

The repository contains a `.dockerignore` file to prevent unnecessary development files from entering the Docker build context.

Examples include:

- `.venv`
- Python cache files
- test cache
- coverage files
- IDE files
- `.env`

## Environment configuration

`.env` is not committed to the repository.

An `.env.example` file is provided instead.

This allows configuration to be documented without committing local environment configuration.

---

# 7. CD / Container Image Delivery

The CD workflow builds the application container image and publishes it to **GitHub Container Registry (GHCR)**.

Images are tagged using the Git commit SHA and `latest`.

The final CD workflow completed successfully in GitHub Actions.

The project does not require a paid hosting provider to satisfy the assignment. The assignment requires a Git repository containing the application, container configuration, pipeline, and documentation. The local Docker Compose environment provides the required runnable application and logging visualization.

---

# 8. How to start the whole environment

## Prerequisites

Install:

- Docker Desktop
- Git

Python and a local virtual environment are useful for development and testing, but the complete runtime environment can be started using Docker Compose.

## Environment configuration

Create `.env` from `.env.example` if it does not already exist.

Example:

```powershell
Copy-Item .env.example .env
```

The `.env` file is ignored by Git.

## Start

From the repository root:

```powershell
docker compose up -d
```

Check the running containers:

```powershell
docker compose ps
```

Expected services:

```text
devsecops-app
devsecops-loki
devsecops-promtail
devsecops-grafana
```

## Application

API:

```text
http://localhost:8000
```

Swagger/OpenAPI documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Grafana

Grafana:

```text
http://localhost:3000
```

Use the Grafana administrator credentials configured during first startup.

The Loki data source is provisioned automatically.

## Stop the environment

```powershell
docker compose down
```

The Grafana named volume is retained when containers are stopped or recreated unless volumes are explicitly removed.

---

# 9. Development checks

Create/activate a Python virtual environment and install the development dependencies:

```powershell
pip install -e ".[dev]"
```

Run the local quality/security checks:

```powershell
ruff check .
pytest
pip-audit
```

The Docker image can be built with:

```powershell
docker build -t devsecops-crud:test .
```

The resulting container can be run with:

```powershell
docker run --rm devsecops-crud:test
```

---

# 10. Tools used and why

## FastAPI

FastAPI was selected because it provides:

- simple API development
- automatic request validation
- OpenAPI documentation
- good Python typing support

## Pydantic

Used for validating API input and defining the Product models.

## Pytest

Used for automated application testing and coverage measurement.

## Ruff

Used for Python linting and code quality checks.

## Docker

Used to package the application into a reproducible container.

## Docker Compose

Used to run the application and complete logging stack with a single command.

## Grafana Loki

Used as the centralized log aggregation backend.

## Promtail

Used to collect Docker container logs and send them to Loki.

## Grafana

Used to visualize and query the collected logs through a browser.

## GitHub Actions

Used to automate CI/CD directly from the Git repository.

## pip-audit

Used to identify known vulnerabilities in Python dependencies.

## Trivy

Used to scan the final Docker image for operating-system and language-specific vulnerabilities.

---

# 11. What would be changed or added with more time

The following are **future improvements and were not implemented in the current version**.

## Application security

- authentication and authorization
- rate limiting
- additional HTTP security headers
- more extensive API abuse protection
- structured JSON logging
- request/correlation IDs

## Data layer

The assignment specifically requires in-memory storage. A production application would replace this with a persistent database with migrations, transaction handling, backups, and secure credential management.

## Container hardening

Potential future hardening could include:

- read-only application filesystems
- dropping unnecessary Linux capabilities
- pinning base images by digest
- resource limits
- further hardening of the logging containers

## Observability

The logging environment could be extended with:

- Prometheus metrics
- application metrics
- dashboards
- alerting
- distributed tracing

## CI/CD improvements

The pipeline could additionally implement:

- SBOM generation
- image signing
- provenance/attestation
- deployment to a staging environment
- deployment approval gates
- automated rollback
- infrastructure-as-code

## Production deployment

A future version could deploy the container image to a cloud/container platform or Kubernetes environment.

A public deployment was not implemented because it is not required by the assignment's stated delivery requirements.

---

# 12. Repository structure

Important project files and directories include:

```text
.
├── .github/
│   └── workflows/
├── app/
│   ├── logging_config.py
│   ├── main.py
│   ├── models.py
│   └── repository.py
├── grafana/
│   └── provisioning/
├── loki/
│   └── loki-config.yml
├── promtail/
│   └── promtail-config.yml
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

# 13. Requirement checklist

| Assignment requirement | Implementation |
|---|---|
| CRUD application | FastAPI REST API |
| One resource | Product |
| Minimum 3 fields | ID, name, category, price |
| In-memory storage | Python dictionary |
| Minimum 2000 records | 2000 products loaded at startup |
| List endpoint | `GET /products` |
| Details endpoint | `GET /products/{product_id}` |
| Add endpoint | `POST /products` |
| Edit endpoint | `PUT /products/{product_id}` |
| Delete endpoint | `DELETE /products/{product_id}` |
| Large dataset handling | Bounded pagination using limit/offset |
| Diagnostic logging | Application and Uvicorn logging |
| Dockerfile | Implemented |
| Docker Compose | Implemented |
| Application in Compose | Implemented |
| Log collection | Promtail + Loki |
| Log visualization | Grafana |
| Single-command startup | `docker compose up -d` |
| Browser access | Application on port 8000, Grafana on port 3000 |
| CI/CD | GitHub Actions |
| Secure delivery stages | Testing, linting, dependency and container scanning |
| Quality Gate | Implemented |
| README documentation | This document |
| Git repository delivery | Implemented |

---

# 14. Conclusion

The project provides a complete DevSecOps environment around a small CRUD application.

The implementation includes:

- a working FastAPI CRUD API
- 2000 in-memory records loaded at startup
- paginated API responses
- input validation
- diagnostic application logging
- Docker containerization
- non-root application execution
- Docker Compose orchestration
- centralized logging using Promtail and Loki
- Grafana log visualization
- automated tests
- Ruff code-quality checks
- Python dependency security scanning
- Docker image vulnerability scanning
- CI quality gates
- automated container image delivery through CD

The repository contains the application code, container configuration, logging stack, GitHub Actions pipeline, security checks, and documentation required for the DevSecOps assignment.
