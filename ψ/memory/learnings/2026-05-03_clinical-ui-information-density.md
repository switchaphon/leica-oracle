# Clinical UI: Information Density is a Feature

**Date**: 2026-05-03
**Source**: rrr --deep: pops-clinic-oracle
**Confidence**: High (confirmed by user twice)

## Pattern

In clinical/medical UX, the OPD consultation header should mirror the full pet profile — not a reduced version. Vets want all patient data visible without navigating away during consultation.

**Include in OPD header:**
- Profile photo
- Species, breed, gender, age, weight
- Visit type (appointment/walk-in/referral)
- Behavior/FAS score (color-coded: Red/Yellow/Green → red/amber/green chips)
- Allergies (red warning chips)
- Clinical note (truncated)

**Don't strip down for "clean UI"** — in clinical contexts, missing info = missed safety signals (allergies, FAS aggression warnings).

## FAS Color Mapping (reusable)

| FAS Level | Color | Tailwind |
|-----------|-------|----------|
| Green (0pts) | Green | `bg-green-50 text-green-700 border-green-200` |
| Yellow (1pt) | Amber | `bg-amber-50 text-amber-700 border-amber-200` |
| Red (2-3pts) | Red | `bg-red-50 text-red-700 border-red-200` |

This score-to-severity-color pattern will recur across vitals, lab results, and triage indicators.

## Tags
`clinical-ux` `information-density` `pet-profile` `fas-score` `allergy` `safety`
