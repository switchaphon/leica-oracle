# Lesson Learned: Self-Hosted CI/CD Infrastructure Migration

**Date**: 2026-07-01
**Source**: Phase 3 CI/CD — pawrent migration to GitLab CE + kubeadm
**Confidence**: High (verified in production-like environment)

## Patterns

### 1. API over CLI in CI/CD Pipelines
**Pattern**: Use HTTP API calls directly instead of vendor CLI tools in CI scripts.
**Why**: CLI versions drift across servers. Infisical CLI v0.38 vs v0.161 broke 4 different approaches before we gave up and used curl. The API contract is stable; the CLI is a moving target.
**Confidence**: 95% — This applies to any self-hosted tool (Vault, Infisical, MinIO mc, etc.)

### 2. Single Source of Truth for k8s Environment Variables
**Pattern**: Never mix ConfigMap (`envFrom`) and Secret (`env: secretKeyRef`) for the same key in a Deployment.
**Why**: Secret silently overrides ConfigMap. No warning, no log. `LINE_CHANNEL_ID: placeholder` in the Secret overrode the correct value in the ConfigMap for hours.
**Anti-pattern**: Dual source → silent override → wrong value → mysterious auth failures.
**Confidence**: 100% — Observed directly, caused 2+ hours of debugging.

### 3. Check Tool Versions Before Writing CI
**Pattern**: Run `<tool> --version` on every target server before writing CI YAML that depends on it.
**Why**: `infisical --version` → v0.38.0 would have immediately shown incompatibility. Instead we wrote CI, pushed, waited 10 min for build, saw failure, iterated. 4 times.
**Confidence**: 90% — Simple discipline, high ROI.

### 4. Infisical Self-Hosted API Pattern
**Pattern**: Login via `/api/v1/auth/universal-auth/login`, export via `/api/v3/secrets/raw`.
**Implementation**:
```bash
TOKEN=$(curl -sf -X POST "https://infisical.pops.vet/api/v1/auth/universal-auth/login" \
  -H "Content-Type: application/json" \
  -d '{"clientId":"$ID","clientSecret":"$SECRET"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")
curl -sf "https://infisical.pops.vet/api/v3/secrets/raw?environment=dev&workspaceId=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; [print(f'{s[\"secretKey\"]}={s[\"secretValue\"]}') for s in json.load(sys.stdin)['secrets']]" > .env
```
**Confidence**: 100% — Working in production.

### 5. LIFF Token TTL Awareness
**Pattern**: LINE LIFF id_token expires in ~1 hour. Browser caches old tokens. Always use incognito for auth testing.
**Why**: Spent 15+ minutes multiple times debugging "401 Invalid LINE token" that was just an expired cached token.
**Confidence**: 100% — Confirmed via LINE API: `{"error":"invalid_request","error_description":"IdToken expired."}`

### 6. MinIO Public URL Needs Ingress Route
**Pattern**: If `S3_PUBLIC_URL` points to the app domain (e.g., `pawrent-dev.pops.pet/storage`), you need a Traefik IngressRoute with `stripPrefix` middleware to route `/storage` → `minio:9000`.
**Confidence**: 100% — Without this, all MinIO-stored images return 404.

## Connections to Past Learnings

- Relates to [[feedback_full_validation_gate]] — pipeline failures from skipping format/lint checks
- Relates to [[project_ci_e2e_deferred]] — E2E still deferred, added more env-specific issues to watch for
- Extends [[feedback_format_check_before_push]] — format before commit prevents wasted CI iterations

## Tags
`cicd`, `gitlab`, `infisical`, `kubernetes`, `minio`, `liff`, `rate-limiting`, `self-hosted`, `migration`
