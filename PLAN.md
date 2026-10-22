# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — Core FastAPI/React skeleton with health endpoint

Status: done

Acceptance:
- FastAPI backend with /health endpoint
- React + TypeScript + Vite frontend with build/test scripts
- Dockerfiles for backend and frontend
- docker-compose.yaml with Keycloak and volumes
- Backend and frontend tests pass
- README with install/run/test steps

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `Dockerfile.backend`, `Dockerfile.frontend`, `compose.yaml`, `README.md`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### driver-benchmark-api — Driver benchmark API for latency measurements

Status: planned

Acceptance:
- POST /api/v1/benchmarks/run endpoint
- GET /api/v1/benchmarks/{id} endpoint
- SQLite persistence with pagination
- Configurable observation/settle delays (from issue #3971)

Implementation: `backend/app/api/benchmarks.py`, `backend/app/services/benchmark.py`, `backend/app/models/benchmark.py`, `backend/tests/test_benchmarks.py`

Tests: `backend/tests/test_benchmarks.py`

### sandbox-orchestration — Cross-OS sandbox orchestration (lume/VM management)

Status: planned

Acceptance:
- POST /api/v1/sandboxes endpoint
- GET /api/v1/sandboxes endpoint with filtering
- ARM64-compatible Docker image references (from issue #353)
- GHCR publish workflow documentation (from issue #22)

Implementation: `backend/app/api/sandboxes.py`, `backend/app/services/sandbox.py`, `backend/app/models/sandbox.py`, `backend/tests/test_sandboxes.py`

Tests: `backend/tests/test_sandboxes.py`

### hyprland-isolated-input — Hyprland isolated background input configuration

Status: planned

Acceptance:
- Configuration schema for synthetic seat (from issue #3550)
- Operator authorization workflow
- Capability negotiation API

Implementation: `backend/app/api/hyprland.py`, `backend/app/services/hyprland.py`, `backend/app/models/hyprland.py`

Tests: `backend/tests/test_hyprland.py`

### cooperative-cancellation — Cooperative cancellation for in-flight operations

Status: planned

Acceptance:
- Cancellation token propagation
- Partial result return on cancel
- Resource cleanup on session end

Implementation: `backend/app/core/cancellation.py`, `backend/app/services/operation.py`

Tests: `backend/tests/test_cancellation.py`

### frontend-dashboard — React dashboard with benchmark/sandbox workflows

Status: planned

Acceptance:
- Benchmark run/create/results views
- Sandbox list/create views
- Real API client with typed responses
- Loading/error/empty states

Implementation: `frontend/src/api/client.ts`, `frontend/src/components/BenchmarkDashboard.tsx`, `frontend/src/components/SandboxDashboard.tsx`, `frontend/src/pages/Benchmarks.tsx`, `frontend/src/pages/Sandboxes.tsx`

Tests: `frontend/src/components/BenchmarkDashboard.test.tsx`, `frontend/src/components/SandboxDashboard.test.tsx`

### auth-oidc-keycloak — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm import
- Backend session management with HttpOnly cookies
- Frontend PKCE login flow
- Role-based authorization (viewer/operator/admin)

Implementation: `backend/app/core/auth.py`, `backend/app/api/auth.py`, `frontend/src/auth/AuthProvider.tsx`, `frontend/src/auth/useAuth.ts`, `keycloak/realm-export.json`

Tests: `backend/tests/test_auth.py`, `frontend/src/auth/AuthProvider.test.tsx`

