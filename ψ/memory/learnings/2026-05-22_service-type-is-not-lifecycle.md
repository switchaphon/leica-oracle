---
date: 2026-05-22
source: "rrr: pops-clinic-oracle"
concepts: [service-type, taxonomy, data-modeling, lifecycle, vet-domain]
---

# Service Type ≠ Lifecycle State

Service types answer "what service is the animal receiving?" — they are the primary categorization (General Medicine, Specialized Medicine, Non-Medical Services).

Lifecycle states answer "where is the case now?" — IPD (inpatient admission), Boarding/Hotel (overnight stay) are states that cases transfer INTO from service types, not service types themselves.

IPD can't exist on its own — it always originates from OPD or Surgery. It inherits the parent service type's color in the UI. Lab is an order within a visit, not a service type.

This distinction matters for:
- **Data modeling**: service_type is a property of the queue item, not of the lifecycle
- **UI**: chip colors map to 3 service types, not N lifecycle states
- **Feature scoping**: IPD and Boarding are separate features with their own flows, not just another entry in the service dropdown
