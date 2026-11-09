# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- **Hyprland Isolated Input API** (`hyprland-isolated-input` feature)
  - `POST /api/v1/hyprland/seats` - Create synthetic seat with capabilities, seat_name, udev_rules
  - `GET /api/v1/hyprland/seats` - List seats with pagination and filtering by status, operator_id
  - `GET /api/v1/hyprland/seats/{id}` - Get seat details
  - `PATCH /api/v1/hyprland/seats/{id}` - Update seat configuration
  - `POST /api/v1/hyprland/seats/{id}/authorize` - Authorize pending seat (admin action)
  - `POST /api/v1/hyprland/seats/{id}/revoke` - Revoke active seat
  - `DELETE /api/v1/hyprland/seats/{id}` - Delete seat
  - `GET /api/v1/hyprland/seats/{id}/config` - Get Hyprland configuration for seat setup
  - `POST /api/v1/hyprland/seats/{id}/negotiate` - Negotiate capabilities for active seat
  - `GET /api/v1/hyprland/seats/{id}/negotiations` - List capability negotiations
  - `POST /api/v1/hyprland/authorize` - Create operator authorization request
  - `GET /api/v1/hyprland/authorize` - List authorization requests with filtering
  - `GET /api/v1/hyprland/authorize/{id}` - Get authorization request details
  - `POST /api/v1/hyprland/authorize/{id}/approve` - Approve authorization request
  - `POST /api/v1/hyprland/authorize/{id}/deny` - Deny authorization request
  - SQLAlchemy models: HyprlandSeat, HyprlandCapabilityNegotiation, HyprlandAuthorizationRequest
  - Enums: HyprlandSeatStatus, HyprlandCapability, HyprlandOperatorRole
  - 26 comprehensive test cases
  - Addresses issue #3550 (synthetic seat configuration)

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-11-06

### Added
- **Sandbox Orchestration API** (`sandbox-orchestration` feature)
  - `POST /api/v1/sandboxes` - Create sandbox with configurable provider (lume, qemu, firecracker, docker), architecture (amd64, arm64), resources (CPU, memory, disk), ports, and labels
  - `GET /api/v1/sandboxes` - List sandboxes with pagination and filtering by status, provider, architecture
  - `GET /api/v1/sandboxes/{id}` - Get sandbox details
  - `PATCH /api/v1/sandboxes/{id}` - Update sandbox configuration
  - `POST /api/v1/sandboxes/{id}/start` - Start sandbox (simulated)
  - `POST /api/v1/sandboxes/{id}/stop` - Stop sandbox
  - `DELETE /api/v1/sandboxes/{id}` - Delete sandbox
  - `GET /api/v1/sandboxes/{id}/ports` - Get port mappings
  - ARM64-compatible Docker image references (addresses issue #353)
  - GHCR image reference support (addresses issue #22)
  - SQLite persistence with SQLAlchemy models
  - 15 comprehensive test cases

## [1.1.0] - 2026-11-02

### Added
- **Driver Benchmark API** (`driver-benchmark-api` feature)
  - `POST /api/v1/benchmarks` - Create benchmark run
  - `GET /api/v1/benchmarks` - List benchmarks with pagination
  - `GET /api/v1/benchmarks/{id}` - Get benchmark details
  - `POST /api/v1/benchmarks/{id}/run` - Execute benchmark (simulated latency measurements)
  - `POST /api/v1/benchmarks/{id}/cancel` - Cancel running benchmark
  - Configurable observation/settle delays and poll interval (addresses issue #3971)
  - SQLite persistence with detailed iteration tracking
  - Percentile latency calculations (p50, p95, p99)
  - 7 comprehensive test cases

## [1.0.0] - 2026-11-01

### Added
- **Core FastAPI/React Skeleton** (`core-skeleton` feature)
  - FastAPI backend with `/api/v1/health` and `/api/v1/ready` endpoints
  - React + TypeScript + Vite frontend with basic structure
  - Dockerfiles for backend and frontend
  - docker-compose.yaml with Keycloak, backend, frontend services
  - SQLite database with SQLAlchemy async ORM
  - Configuration via pydantic-settings
  - CORS middleware for frontend integration
  - Structured logging with structlog
  - Health and readiness checks
  - Backend and frontend test infrastructure
