# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-22

### Added
- Initial project structure with FastAPI backend and React/TypeScript/Vite frontend
- Health check endpoints (`/api/v1/health`, `/api/v1/health/ready`)
- Docker Compose with backend, frontend, and Keycloak services
- Keycloak realm export with viewer/operator/admin roles
- Placeholder API routes for benchmarks, sandboxes, Hyprland, and auth
- Frontend pages: Dashboard, Benchmarks, Sandboxes, Hyprland, Login
- Typed API client with cookie-based authentication
- Basic test suite for backend and frontend
- README with architecture diagram and API reference
- MIT License

### Security
- HttpOnly SameSite cookies for session management
- CSRF protection on state-changing operations
- Role-based authorization framework
- Demo mode restricted to localhost

### Infrastructure
- Non-root Docker users
- Health checks for all services
- Persistent volumes for database and Keycloak data
- ARM64-compatible base images