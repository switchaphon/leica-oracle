---
title: WARNING_* is a new non-blocking prefix convention in nodered-simulator. ERROR_* 
tags: [convention, naming, measurement-keys, error-handling, mqtt]
created: 2026-06-05
source: rrr: nodered-simulator-oracle
project: github.com/switchaphon/nodered-simulator-oracle
---

# WARNING_* is a new non-blocking prefix convention in nodered-simulator. ERROR_* 

WARNING_* is a new non-blocking prefix convention in nodered-simulator. ERROR_* keys trigger hasError and pump forced-stop via the `sensorKey.startsWith('ERROR_')` loop. WARNING_* keys are intentionally excluded — they are informational MQTT flags that do not block device operation. Future warning keys for other device types should follow this convention. If a warning needs to trigger forced-stop, the error detection loop must be explicitly modified.

---
*Added via Oracle Learn*
