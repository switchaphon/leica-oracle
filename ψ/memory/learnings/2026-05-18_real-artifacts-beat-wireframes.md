---
name: real-artifacts-beat-wireframes
description: Real hospital forms and physical artifacts are more informative than Figma wireframes for clinical workflow design
metadata:
  type: learning
  date: 2026-05-18
  source: imaging-order-prp-grill
---

## Pattern

When designing clinical workflows (X-ray ordering, lab requests, etc.), a single photo of a real hospital form reveals more truth than multiple high-fidelity wireframes.

## Evidence

- Figma wireframes (3 nodes, 5M chars of design context) showed 6 X-ray body regions
- Real yellow carbon X-ray request form showed 8 regions — Joint, Bone, Vertebrae were missing from Figma
- Real form revealed Thorax splits Rt Lat / Lt Lat (clinically significant for cardiac evaluation)
- Real form had Special Studies section (contrast studies) not represented in Figma at all
- Real form showed Joint/Bone need a write-in line (free text) for specifying which joint/bone

## Lesson

Always ask for real-world clinical artifacts (paper forms, existing software screenshots, workflow photos) BEFORE committing to a digital design. Wireframes reflect designer intent; real forms reflect clinical practice accumulated over decades.

## Applied

The PRP uses the 8 regions from the real form, not the 6 from Figma. Special Studies included. Joint/Bone laterality + free text captured.
