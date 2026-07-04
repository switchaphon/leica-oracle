# Cite Sources in Clinical Systems

**Date**: 2026-05-02
**Source**: User challenged "reference มาจากไหน?" on SOAP-to-slash-command mapping
**Confidence**: High (corrected in session)

## Pattern

In clinical/medical software, every design decision that maps to clinical workflow must trace back to a documented standard or design artifact — not AI inference. Even when intuition is correct, present the reference alongside the recommendation.

## Evidence

Proposed SOAP section → slash command mapping based on general veterinary knowledge. User asked for the reference source. Found it matched `pops-gem/soap_note_template.md` (Oct 2025) exactly — but should have cited it from the start, not after being challenged.

## When to Apply

- Any mapping between clinical concepts and UI/system behavior
- When recommending command structure, workflow order, or data model decisions for medical records
- Always check pops-gem/ and docs/ for existing references before inferring

## Anti-pattern

"Based on standard SOAP practice..." without citing which standard, which document, which section. In a PIMS, provenance is as important as correctness.
