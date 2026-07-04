# Documentation as Architecture Tool

**Date**: 2026-05-22
**Context**: Writing entity lifecycle docs for POPs clinic prototype
**Source**: rrr: pops-app-vet

## Lesson

Writing lifecycle documentation for each entity (Queue, Appointment, OPD, Diagnostic, Prescription, Invoice, Receipt) exposed a structural problem that wasn't visible during development: Queue status was absorbing OPD-specific states (WAITING_LAB, WAITING_DISPENSING, CANCELLED_TREATMENT).

This only became visible when we asked "does this Queue status make sense for Grooming?" and the answer was no for 3 of 9 statuses.

## Principle

**Document the lifecycle of every entity as if it must work for a service type that doesn't exist yet.** If the status model breaks when you substitute a different consumer, the abstraction is leaking.

## Application

- Queue should be a generic service pipeline: CHECKED → WAITING → IN_SERVICE → WAITING_PAYMENT → COMPLETED
- Service-specific states belong on the service entity (OPD, Grooming, etc.)
- Cross-cutting visibility (e.g., "which queues are waiting for lab") should be resolved via query/join, not by polluting the generic status model

## Tags

architecture, documentation, abstraction-leak, queue, opd, lifecycle, separation-of-concerns
