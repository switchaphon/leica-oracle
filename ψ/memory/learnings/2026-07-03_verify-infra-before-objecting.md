# Verify infra capabilities before objecting on infra grounds

**Date**: 2026-07-03
**Source**: AI platform grill session (pops/ai, 5 ADRs)
**Confidence**: High (flipped a real architecture decision)

## The mistake class

Two mistakes in one session, same root cause: making platform-level claims from default assumptions instead of checking the org's actual state.

1. Objected to polyrepo microservices with "shared middleware needs a private package registry, infra you don't have." Wrong: git.pops.vet is self-hosted GitLab, which ships a PyPI-compatible package registry, container registry (registry.pops.vet), CI runners, and Pages built in. GitHub-flavored defaults applied to a GitLab org.
2. Declared "one consumer, no gateway trigger" while Pawrent's vaccine-sticker upload (which makes Pawrent Consumer #2) was already under development. Roadmap fact the user held; never asked.

## The guards

- Before objecting on infra grounds: verify what the org's infra actually provides (self-hosted GitLab ~= GitHub + registry + CI + Pages for free).
- Before any "do we need X yet?" architecture call: ask about in-flight work on sibling products first. The trigger may already be pulled.
- No compliance claim without a read in the same turn (caught 6/7 vs claimed 7/7 conventions this same session).

## Heuristics promoted this session

- **"Data ownership decides the caller"** - whoever owns the input data calls the AI service; result distribution goes through the data owner's backend.
- **"Services scale with env vars; consumers scale with a gateway"** - service count is a config problem, consumer count is a platform problem.

## Reusable technique

Grill-emits-artifacts: during /grill-with-docs, write each resolved decision into ADR/CONTEXT/contract files the moment it lands. The interview is the documentation pass; being overruled becomes a recorded Considered-Option instead of a lost argument.
