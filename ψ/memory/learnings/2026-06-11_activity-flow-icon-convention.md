---
pattern: Activity flow icons in prototype index should match their origin base page, not the action they perform
context: Un corrected 5 activity flow icons — OPD flows should use FolderOpen (same as OPD base), Queue flows should use ListOrdered (same as Queue base). Icons like Syringe/Pill/Banknote describe the action but make it harder to scan flows by entry-point.
resolution: icon = where it starts. OPD→FolderOpen, Queue→ListOrdered, Dashboard→House, Diagnostic→Microscope, Pet→PawPrint. The action is already in the title text.
tags: [prototype-index, icon-convention, design-system, navigation]
---

## Rule

Activity flow icon = origin base page icon, NOT action icon.

| Origin | Icon | NOT |
|--------|------|-----|
| OPD | FolderOpen | Syringe, Pill, Stethoscope |
| Queue | ListOrdered | Banknote, Receipt |
| Dashboard | House | — |
| Diagnostic | Microscope | FlaskConical |
| Pet Profile | PawPrint | — |

## Why

When scanning the activity flow grid, users want to group by "where do I start?" not "what does it do?" The title already says "OPD → Add Service Fees" — the icon just reinforces the entry-point.
