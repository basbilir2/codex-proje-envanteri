# Local AI OS 0.5.0 — Verification

Date: 2026-08-16

Final executable: `release/LocalAIOS.exe`

- Size: 51,645,367 bytes
- SHA-256: `D725F364F6188E812E5D50DC340817DA6C0B13981C0A3FA5ECA390EE2968900F`

- Normal startup and Qwen3 14B loading: passed.
- Real local Qwen3 14B greeting: passed in 12.8 seconds.
- Instant greeting route in the real Windows chat UI: passed in under one second.
- Fast/Balanced/Powerful reasoning selection: passed.
- Long-running work changes Send to Stop; cancellation returned the UI to ready state: passed.
- Parallel live internet retrieval: four sources in 2.7 seconds.
- Responsive message box and visible Send button at the tested window size: passed.
- Earlier full coverage remains passed: sourced memory, capability acquisition/routing, portable profile, mini-app generation and final image generation.

Reports:

- `release/performance-test-report.json`: real-model, routing and parallel-retrieval timing evidence.
- `release/self-test-report.json`: complete functional run evidence.
- `release/image-test-report.json`: final image test evidence.
