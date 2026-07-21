---
title: Oracle repos and project repos serve different purposes. Oracle repos hold conte
tags: [oracle-boundary, repo-organization, operational-docs, workspace-geography]
created: 2026-05-23
source: rrr: rpro-saas-oracle
project: github.com/switchaphon/rpro-saas-oracle
---

# Oracle repos and project repos serve different purposes. Oracle repos hold conte

Oracle repos and project repos serve different purposes. Oracle repos hold context, memory, decisions, and retrospectives. Project repos hold operational artifacts — incident postmortems, runbooks, deployment guides, API docs. Writing operational docs into the oracle repo just because "that's where the investigation happened" is an anti-pattern. The oracle investigates; the project owns the artifacts. On this machine: ~/ghq/ = Oracle repos only, /Users/switchaphon/_RPRO_/ = actual project source code.

---
*Added via Oracle Learn*
