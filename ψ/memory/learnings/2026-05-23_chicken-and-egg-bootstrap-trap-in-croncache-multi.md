---
title: Chicken-and-Egg Bootstrap Trap in Cron+Cache Multi-Tenant Systems: When a cron j
tags: [multi-tenancy, redis, chicken-and-egg, cron, debugging, rpro-saas, bootstrap, fresh-cluster, incident-response, cache-dependency]
created: 2026-05-23
source: rrr --deep: rpro-saas-oracle
project: github.com/switchaphon/rpro-saas-oracle
---

# Chicken-and-Egg Bootstrap Trap in Cron+Cache Multi-Tenant Systems: When a cron j

Chicken-and-Egg Bootstrap Trap in Cron+Cache Multi-Tenant Systems: When a cron job populates a cache (Redis) that a write operation depends on, the system cannot bootstrap from zero. In rpro-saas, ts-cron-service populates Redis station_tenant every 15 min from station DB. StationValidateDuplicate reads this cache and throws on empty. Fresh cluster = no stations = empty Redis = can't create first station = infinite loop. Feature RPRO-12731 was tested on cluster with existing data — fresh-cluster scenario was invisible. Fix: catch empty Redis gracefully (return {} instead of throw), or seed Redis before first station creation. Debugging shortcut: for "identical code, different behavior" bugs, compare observable state (HGETALL, SELECT COUNT) BEFORE tracing code. Cascading errors from one root cause look like multiple problems — fix the first error chronologically, then re-test.

---
*Added via Oracle Learn*
