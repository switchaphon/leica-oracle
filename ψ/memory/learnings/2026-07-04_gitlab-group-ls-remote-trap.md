# Lesson: GitLab group ls-remote returns group HEAD, not project HEADs

**Date**: 2026-07-04
**Source**: Probing `pops/backend/microservices/*` for repos — `git ls-remote HEAD` returned valid hashes for ANY name, including `unicorn-service` and `pizza-service`. Clone failed with 404.
**Confidence**: High (verified with fake names)

## Pattern

`git ls-remote <group-url>/<any-name>.git HEAD` on GitLab can return the **group's own HEAD** rather than 404 when auto-project-creation is enabled or the group has its own repository. This produces false positives.

## How to verify

```bash
# WRONG — false positives
git ls-remote https://gitlab.example.com/group/subgroup/repo.git HEAD

# RIGHT — clone actually fails if repo doesn't exist
git clone --depth 1 <url> /tmp/test && echo "REAL" || echo "FAKE"

# BEST — full ls-remote (no HEAD filter) returns nothing for fake repos
git ls-remote https://gitlab.example.com/group/subgroup/repo.git
```

## Workaround without API

Clone a known repo that references others (e.g., a deployment/CI repo that lists all services) and read the service list from its directory structure.

## Related

[[branch-survey-before-building]] — same theme: verify before assuming.
