# Victus AI 2.0 — Complete Repository Analysis & Security Assessment

**Date:** 2026-03-18
**Assessor:** Automated Security & Engineering Review
**Scope:** Full codebase analysis — architecture, code quality, vulnerabilities, and improvements

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Tech Stack](#2-architecture--tech-stack)
3. [Scope & Feature Map](#3-scope--feature-map)
4. [Code Quality Assessment](#4-code-quality-assessment)
5. [Security & Vulnerability Assessment](#5-security--vulnerability-assessment)
6. [Testing Assessment](#6-testing-assessment)
7. [Improvement Recommendations](#7-improvement-recommendations)
8. [Summary & Risk Matrix](#8-summary--risk-matrix)

---

## 1. Project Overview

**Victus AI 2.0** is a **local-first personal AI assistant** with a FastAPI backend and React frontend. It provides policy-gated orchestration across multiple domains: memory management, personal finance tracking, filesystem sandboxing, camera tooling, and mail intelligence.

### Key Principles
- **Local-first**: All data stored on the user's machine — no cloud sync
- **Policy-supreme**: Every tool execution passes through a policy engine; security policy cannot be bypassed
- **Domain-driven**: Clean separation into orchestrator, finance, memory, filesystem, camera, and mail domains
- **Phase-based development**: Built incrementally across 4 phases (Baseline → Security Hardening → Camera MVP → Adaptive UI)

### Repository Structure

```
Victus/
├── apps/
│   ├── local/main.py              # FastAPI entrypoint
│   └── web/                       # React + Vite + TypeScript frontend
│       ├── src/
│       │   ├── components/        # UI components (Lanes, widgets, drawer)
│       │   ├── views/             # Screen views (Memory, Files, Camera, Finance)
│       │   ├── engine/            # Adaptive scoring and layout engine
│       │   ├── api/               # API client
│       │   └── store/             # State management
│       └── e2e/                   # Playwright E2E tests
├── core/
│   ├── orchestrator/              # Intent routing, policy engine, confidence gating
│   ├── finance/                   # Finance service, policy, schemas
│   ├── filesystem/                # File sandbox service
│   ├── logging/                   # Audit logging, redaction, sanitization
│   ├── vault/                     # Vault sandbox
│   ├── memory/                    # Memory service and storage
│   ├── security/                  # Auth, bootstrap store, API keys
│   ├── camera/                    # Camera service and backends
│   ├── domains/                   # Domain handlers
│   ├── signals/                   # Signal extractors
│   ├── storage/                   # Database connection (SQLite)
│   └── config.py                  # All configuration classes
├── victus/
│   ├── ui/                        # UI rendering
│   ├── ui_state/                  # UI state service
│   ├── finance/                   # Finance models & DB
│   ├── domains/                   # Productivity & system plugins
│   └── core/                      # Confidence, failures, memory, CLI
├── victus_local/                  # Compatibility module (legacy + unit test support)
├── adapters/
│   ├── llm/provider.py           # LLM provider (OpenAI / Ollama)
│   └── runtime/launcher.py       # Subprocess launcher
├── tests/                         # Pytest unit & regression tests
├── docs/                          # Architecture, security, dev guide, etc.
├── scripts/                       # Quality report, contract check
└── .github/workflows/ci.yml      # GitHub Actions CI
```

---

## 2. Architecture & Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11–3.12, FastAPI, Uvicorn, Pydantic |
| **Frontend** | React 18.3, Vite 5.4, TypeScript 5.6, TailwindCSS |
| **Database** | SQLite (local file) |
| **LLM Integration** | OpenAI API, Ollama (local fallback) |
| **Auth** | Custom JWT with bcrypt KDF |
| **Testing** | Pytest, Vitest, Playwright |
| **CI/CD** | GitHub Actions (lint, test, coverage across Python 3.11/3.12) |
| **Linting** | Ruff (check + format), pre-commit hooks |
| **Desktop** | PySide6 (optional GUI) |

### API Endpoints (18+ routes)

| Category | Endpoints |
|----------|-----------|
| **Auth** | `POST /login`, `GET /bootstrap/status`, `POST /bootstrap/init`, `GET /me` |
| **Memory** | `POST /memory/add`, `GET /memory/search`, `GET /memory/list`, `DELETE /memory/{id}` |
| **Finance** | `POST /finance/add`, `GET/PATCH/DELETE /finance/transactions/{id}`, `GET /finance/summary`, spending/category summaries, alerts, rules |
| **Files** | `GET /files/list`, `GET /files/read`, `POST /files/write` |
| **Camera** | `GET /camera/status`, `POST /camera/capture`, `POST /camera/recognize` |
| **Orchestration** | `POST /orchestrate`, `GET /debug/orchestrator` |
| **UI** | `GET /api/ui/state`, approvals, reminders, workflows, dialogue |

---

## 3. Scope & Feature Map

### Core Domains

| Domain | Description | Status |
|--------|-------------|--------|
| **Orchestrator** | Intent routing with confidence gating, deterministic fallback, LLM-assisted routing | Active |
| **Memory** | Semantic memory storage with sensitivity levels (public/internal/sensitive/critical), search, retention | Active |
| **Finance** | Transaction CRUD, spending analysis, category summaries, rule-based alerts, AI-powered briefs | Active |
| **Filesystem** | Sandboxed file read/write with path traversal protection, extension allowlist | Active |
| **Camera** | Multi-backend camera capture and object recognition (OpenCV / stub) | Active |
| **Mail Intelligence** | Mail connector and intelligence analysis | Scaffolded |
| **Cognition** | Decision advisor models | Scaffolded |
| **Productivity** | LLM plugins, document writing, task automation | Active |
| **System** | Status, app launching, network info (strict allowlist) | Active |

### Security Features

| Feature | Implementation |
|---------|---------------|
| **Authentication** | Custom JWT with bcrypt KDF signature |
| **Bootstrap** | One-time admin setup with 12-char minimum password |
| **Sensitivity Model** | 4-level memory sensitivity classification |
| **Redaction** | Automatic regex-based secret redaction in logs |
| **Policy Engine** | Allowlist-based tool execution gating |
| **Sandbox** | Filesystem isolation with symlink escape detection |
| **Audit Logging** | Timestamped audit events for auth and policy |
| **Error Handling** | Dev/prod mode separation for error messages |

---

## 4. Code Quality Assessment

### Strengths

1. **Clean modular architecture** — clear separation of concerns across core/, victus/, adapters/, apps/
2. **Pydantic models everywhere** — strong typing and validation at API boundaries
3. **Policy-first design** — execution requires policy approval, preventing unauthorized actions
4. **Comprehensive documentation** — architecture.md, security-hardening.md, DEV_GUIDE.md, POLICY.md, and domain-specific docs
5. **Pre-commit hooks** — Ruff linting/formatting enforced before commits
6. **CI pipeline** — Multi-version Python testing with coverage reporting
7. **Layered error handling** — Safe user-facing errors vs. detailed dev errors

### Weaknesses

1. **No Docker support** — no containerization for consistent deployment
2. **No database migrations** — schema changes require manual handling
3. **Mixed legacy code** — `victus_local/` contains compatibility shims alongside active code
4. **No API versioning** — endpoints lack version prefix (e.g., `/v1/`)
5. **Limited connection management** — SQLite connections created per-query, no pooling
6. **No OpenAPI schema export** — while FastAPI auto-generates docs, no versioned schema file is maintained

---

## 5. Security & Vulnerability Assessment

### CRITICAL Severity

#### C1: Non-Standard JWT Implementation
**Location:** `core/security/auth.py`

**Issue:** Uses bcrypt.kdf for token signatures instead of standard HMAC-SHA256. This is:
- Non-standard and unaudited
- Computationally expensive (potential DoS vector on every token verification)
- Not compatible with any JWT ecosystem tooling

```python
signature = bcrypt.kdf(
    password=payload_b64.encode("utf-8"),
    salt=secret.encode("utf-8"),
    desired_key_bytes=32,
    rounds=64,
)
```

**Recommendation:** Replace with PyJWT using HS256 algorithm.

#### C2: Arbitrary Executable Execution
**Location:** `victus_local/task_runner.py:44`

**Issue:** Directly executes file paths as subprocesses:
```python
subprocess.Popen([str(path)])  # Direct path execution
```
While `resolve_app_name()` validates through a dictionary, a compromised dictionary or path resolution could lead to arbitrary code execution.

**Recommendation:** Strict allowlist validation of resolved paths before execution.

#### C3: API Key Exposed in URL Query String
**Location:** `victus_local/media_router.py:170`

**Issue:** YouTube API key is passed in URL query parameters, which get logged by servers, proxies, and browsers:
```python
url = f"...&key={api_key}"
```

**Recommendation:** Use Authorization header for API key transport.

---

### HIGH Severity

#### H1: SQL Injection in GROUP BY Clauses
**Location:** `core/finance/store.py:77-85`

**Issue:** Column names interpolated directly into SQL:
```python
sql = f"SELECT {group_by} as key, SUM(amount_cents) as total FROM transactions WHERE 1=1"
sql += f" GROUP BY {group_by}"
```
While an allowlist check exists, the pattern is fragile and could break if allowlists are extended carelessly.

**Recommendation:** Use explicit column mapping dict instead of string interpolation.

#### H2: No Rate Limiting
**Issue:** No rate limiting on `/login`, `/bootstrap/init`, or any API endpoint. Brute-force attacks against authentication are trivially possible.

**Recommendation:** Add `slowapi` or similar rate limiting middleware.

#### H3: Unencrypted Data at Rest
**Issue:** SQLite databases and memory JSON files stored in plaintext:
- `victus_data/memory/victus_memory.json` — plaintext
- Finance database — unencrypted SQLite
- Sensitive memories marked "critical" still stored unencrypted

**Recommendation:** Use SQLCipher for encrypted SQLite or application-level encryption for sensitive records.

#### H4: No CSRF Protection
**Issue:** State-changing endpoints (POST/PATCH/DELETE) lack CSRF tokens. Combined with `allow_credentials=True` in CORS, this is exploitable.

**Recommendation:** Implement CSRF tokens for all state-changing operations.

---

### MEDIUM Severity

#### M1: CORS Misconfiguration
**Location:** `apps/local/main.py:155-161`

```python
allow_methods=["*"],   # Overly permissive
allow_headers=["*"],   # Overly permissive
```

**Recommendation:** Explicitly list required methods and headers.

#### M2: Missing HTTP Security Headers
**Issue:** No Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, or Referrer-Policy headers.

**Recommendation:** Add security headers middleware.

#### M3: Session Cookie Configuration
**Location:** `victus_local/admin_auth.py`

**Issue:** `SameSite=Lax` should be `Strict` for admin operations. Session tokens exist only in memory (lost on restart).

#### M4: Weak Password Policy
**Issue:** Bootstrap requires only 12 characters — no complexity requirements (uppercase, numbers, symbols).

#### M5: No Input Length Limits on Messages
**Location:** `victus_local/server.py:152-154`

**Issue:** Message input only checks for non-empty, no maximum length validation. Could lead to memory exhaustion or LLM abuse.

---

### LOW Severity

#### L1: Error Information Leakage
**Issue:** SSE stream in `victus_local/server.py` can return raw exception messages during execution errors in dev mode.

#### L2: No Database Connection Pooling
**Issue:** New SQLite connection created per query — inefficient under load.

#### L3: Spotify Credentials in Python Module
**Issue:** Spotify credentials loaded via `importlib.util.exec_module` from a Python file rather than secure vault.

---

### Positive Security Findings

| Finding | Location |
|---------|----------|
| **Strong path traversal protection** | `core/filesystem/sandbox.py` — comprehensive symlink and escape detection |
| **Secret redaction in logs** | `core/logging/logger.py`, `victus/core/failures/redaction.py` — regex patterns for API keys, tokens, hashes |
| **Allowlist-based policy engine** | `victus/core/policy.py` — whitelist approach, not denylist |
| **Parameterized SQL queries** | Most WHERE clause values use parameterized queries |
| **Pydantic input validation** | API boundaries use constrained Pydantic fields (`ge=1, le=100`) |
| **Dev/prod error separation** | `core/errors.py` — safe messages in prod, detailed in dev |
| **Audit logging** | `core/logging/audit.py` — timestamped auth and policy events |
| **HttpOnly cookies** | Admin session cookies set with `httponly=True` |
| **Extension allowlist** | File operations restricted to `.txt`, `.md`, `.json`, `.csv` |

---

## 6. Testing Assessment

### Current Coverage

| Area | Framework | Status |
|------|-----------|--------|
| **Backend Unit** | Pytest | Active — confidence, memory, finance, camera, policy tests |
| **Backend Regression** | Pytest | Active — router confidence regressions |
| **Frontend Unit** | Vitest | Present |
| **Frontend E2E** | Playwright | Present in `apps/web/e2e/` |
| **Contract Tests** | Custom script | `scripts/contract_check.py` |
| **CI** | GitHub Actions | Python 3.11 + 3.12, lint + test + coverage |

### Testing Gaps

1. **No security-focused tests** — no auth bypass tests, injection tests, or fuzzing
2. **No load/stress tests** — no performance benchmarks or DoS resistance tests
3. **No integration tests** between backend and frontend
4. **No API contract tests** against OpenAPI schema
5. **No dependency vulnerability scanning** (e.g., `safety`, `pip-audit`, `npm audit`)

---

## 7. Improvement Recommendations

### Priority 1 — Security (Immediate)

| # | Action | Effort |
|---|--------|--------|
| 1 | Replace custom JWT with PyJWT (HS256) | Low |
| 2 | Add rate limiting (`slowapi`) on auth endpoints | Low |
| 3 | Fix YouTube API key — use Authorization header | Low |
| 4 | Add HTTP security headers middleware | Low |
| 5 | Implement CSRF protection | Medium |
| 6 | Validate executables in task_runner against strict allowlist | Low |

### Priority 2 — Data Protection

| # | Action | Effort |
|---|--------|--------|
| 7 | Encrypt sensitive data at rest (SQLCipher or app-level) | Medium |
| 8 | Add credential rotation mechanism | Medium |
| 9 | Move Spotify credentials to secure env vars | Low |
| 10 | Strengthen password policy (complexity requirements) | Low |

### Priority 3 — Code Quality & Operations

| # | Action | Effort |
|---|--------|--------|
| 11 | Add Docker support for consistent deployment | Medium |
| 12 | Implement database migration system (Alembic) | Medium |
| 13 | Add API versioning (`/v1/` prefix) | Low |
| 14 | Add dependency vulnerability scanning to CI (`pip-audit`, `npm audit`) | Low |
| 15 | Implement connection pooling for SQLite | Low |
| 16 | Add OpenAPI schema versioning | Low |

### Priority 4 — Testing

| # | Action | Effort |
|---|--------|--------|
| 17 | Add security test suite (auth bypass, injection, fuzzing) | Medium |
| 18 | Add load testing (Locust or k6) | Medium |
| 19 | Add backend-frontend integration tests | Medium |
| 20 | Add API contract tests against OpenAPI schema | Low |

---

## 8. Summary & Risk Matrix

### Overall Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Architecture** | Strong | Clean modular design, policy-first approach |
| **Code Quality** | Good | Pydantic models, linting, pre-commit hooks |
| **Documentation** | Good | Comprehensive docs, architecture diagrams |
| **Security** | Needs Work | Custom JWT, no rate limiting, unencrypted data |
| **Testing** | Moderate | Unit + E2E present, but no security or load tests |
| **DevOps** | Basic | CI present, but no Docker, no infra-as-code |

### Risk Matrix

| Risk | Likelihood | Impact | Severity |
|------|-----------|--------|----------|
| Auth bypass via JWT weakness | Medium | Critical | **CRITICAL** |
| Arbitrary code execution (task_runner) | Low | Critical | **CRITICAL** |
| API key leakage (YouTube) | High | Medium | **HIGH** |
| SQL injection (GROUP BY) | Low | High | **HIGH** |
| Brute-force login (no rate limit) | High | Medium | **HIGH** |
| Data theft (unencrypted storage) | Medium | High | **HIGH** |
| CSRF attacks | Medium | Medium | **MEDIUM** |
| XSS via error messages | Low | Medium | **LOW** |

### Final Verdict

Victus AI 2.0 demonstrates **strong architectural foundations** with its policy-gated orchestration, domain separation, and local-first philosophy. The codebase is well-organized with good documentation and CI practices.

However, **the security layer has critical gaps** — particularly the custom JWT implementation, lack of rate limiting, and unencrypted data storage. These should be addressed before any production or multi-user deployment.

The project is best suited as a **single-user local tool** in its current state. For any broader deployment, the Priority 1 and Priority 2 recommendations above are essential prerequisites.

---

*Report generated: 2026-03-18 | Scope: Full repository analysis of Victus AI 2.0*
