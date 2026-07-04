# Lesson: Web Speech API Depends on Google Servers

**Date**: 2026-06-17
**Source**: Speech-to-SOAP MVP debug session
**Tags**: voice, web-speech-api, chrome, network, demo

## Context

User clicked mic FAB in Chrome, recording bar appeared with waveform, but no text was ever transcribed. Console showed `[Voice] SpeechRecognition error: network`. Web Speech API sends audio to Google servers for processing -- if the network path is blocked (VPN, corporate firewall, ISP), the feature silently fails.

## Lesson

Web Speech API (`webkitSpeechRecognition`) is not a local feature. It streams audio to Google's servers over HTTPS. The `network` error means Chrome can't reach those servers. This is not a code bug and cannot be fixed in code.

Always build a mock fallback for any demo that depends on Web Speech API. The mock button should be prominent and easy to enable, not hidden.

## Application

- Demo prep: test Web Speech API on the actual demo network beforehand
- If `network` error: try 127.0.0.1 instead of localhost, check VPN, check firewall
- Phase 2 solution: Whisper API (our server, no Google dependency)
- Phase 3 solution: client-side whisper.cpp (no network at all)
