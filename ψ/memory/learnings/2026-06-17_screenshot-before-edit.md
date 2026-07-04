# Lesson: Screenshot Before Editing UI Elements Described by Appearance

**Date**: 2026-06-17
**Source**: Speech-to-SOAP MVP session
**Tags**: ui, workflow, communication

## Context

User said "panel สีดำ" (black panel). I assumed VoiceRecordingBar and edited 3 files (position, corners, padding). User actually meant the PrototypeGuide bottom bar. Had to revert all 3 edits.

## Lesson

When the user describes a UI element by its visual appearance rather than by component name, take a screenshot first and confirm "this one?" before making any edits. The cost of one screenshot round-trip is much lower than 3 file reverts + the correct edit.

## Application

- User says "the dark bar at the bottom" -> screenshot + highlight + ask
- User says "that pink thing on the right" -> screenshot + ask
- User gives a component name like "VoiceRecordingBar" -> edit directly, no need to ask
