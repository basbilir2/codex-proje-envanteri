# Local AI OS — Project Context

Last updated: 2026-08-16
Current desktop release: 0.5.0

Verification status: real Qwen3 14B chat, live retrieval, sourced memory, capability acquisition/routing, portable profile, mini-app generation, final image generation, reasoning modes, instant greeting and cancellation were exercised on 2026-08-16. See `release/VERIFICATION.md`.

## Product identity

Local AI OS is the user's own general-purpose personal AI. It is not Sipariş Takip, General, Trendy Brander, or a software-project manager. Those are separate products. New abilities belong in optional Local AI OS plugins, not in the identity of the core application.

## Main goal

Create a free Windows AI that ordinary home users can install and use through one chat screen. It must run locally according to available hardware, optionally borrow free online compute when local hardware is insufficient, improve through source-backed experience, and continue on another PC through a portable/synchronized profile.

Universal superiority over every paid frontier model cannot be guaranteed. The engineering target is comparable or better results on selected real workflows through better retrieval, source selection, verification, plugins, personal context, and accumulated experience.

## Core intelligence principle

The system must not try to keep the internet in model weights, RAM, or local storage. Its primary intelligence is learning:

1. What information is actually needed.
2. Where trustworthy/current information can be found.
3. How to retrieve and compare it.
4. How to apply it to the current request.
5. What compact lesson should remain afterward.
6. What temporary or low-value information should be forgotten.

The internet acts as broad external knowledge and optional compute. The local model remains the private decision/processing layer.

## Product rules

- Local-first; usable offline after the initial model setup.
- Executive Brain is orchestration code, not a second always-loaded model.
- Hardware profiler automatically selects a suitable local model.
- Free cloud is optional, replaceable, quota-aware, and not required for core operation.
- Private user content is not sent online without a relevant permission.
- Store source URL + retrieval method + compact lesson + result, not full web pages in RAM.
- Keep only short expiring source chunks for offline continuity and speed.
- Prune old, rarely reused lessons; cap retained lessons.
- Capabilities are versioned plugins. LoRA remains optional and later.
- App, knowledge, and plugin updates must explain what changed and ask before installation.

## Current Windows application

The primary artifact is `release/LocalAIOS.exe`.

Implemented:

- Non-technical chat UI.
- Three reasoning modes: Fast, Balanced and Powerful. Balanced mode automatically reserves deep reasoning for genuinely difficult requests.
- Instant local shortcuts for greetings and thanks; long work can be cancelled from the Send button after it changes to Stop.
- Bounded recent conversation/source context and parallel page retrieval for lower waiting time and memory use.
- First-run automatic download of a local `llama.cpp` engine and GGUF model.
- RAM-based model profiles: Qwen3 1.7B, 4B, 8B, or 14B.
- Local OpenAI-compatible model server managed invisibly by the app.
- Optional OpenRouter `openrouter/free` compute routing; free user key stored in Windows Credential Manager.
- Automatic no-key web research through a public search result feed.
- Retrieval of relevant sections from several result pages.
- Source-first knowledge records with URL, source hash, keywords, summary, refresh date, and expiring query cache.
- A source link supplied inside a task is learned first and the original task then continues in the same chat turn.
- Lesson memory storing the need, learned result, source links, applied capability workflow, reuse count and dates.
- Automatic pruning of low-use lessons older than 180 days and a 300-lesson cap.
- Expired retrieved page chunks are deleted while their compact source route remains.
- Hybrid capability routing: cheap literal triggers first, then local-model semantic matching/gap detection for work requests.
- Chat-driven capability acquisition: internet research + local-model-authored portable recipe.
- Capability recipes store triggers, source paths, reacquisition method, workflow, quality rules, permissions and optional program tools.
- Quality validation and one corrective generation pass for capability-backed answers.
- Plugin installation from JSON or `.lai-plugin` packages through the UI.
- Chat/button image generation and text-generated offline single-file mini applications.
- Manually approved `.lai-plugin` packages may carry isolated relative-path `.exe` program tools; they receive the request over standard input, return bounded output and have a strict timeout. Chat-acquired recipes cannot add executables.
- Built-in end-to-end self-test covering real local inference, live research, memory, capability acquisition, mini app and image output.
- Self-test keeps generated memory/plugins/artifacts in an isolated test data directory while reusing the downloaded model/runtime.
- Portable `.laios` profile export/import.
- Optional profile synchronization through a user-selected OneDrive/Google Drive/other synchronized folder.
- Knowledge/capability-pack and verified EXE update infrastructure; startup shows feature notes and asks before installing.

## Memory layers

- Working memory: current chat/model context only.
- Source map: compact records under `%LOCALAPPDATA%\LocalAIOS\knowledge`.
- Lesson memory: `%LOCALAPPDATA%\LocalAIOS\memory\lessons.json`.
- Plugins: `%LOCALAPPDATA%\LocalAIOS\plugins`.
- Portable/sync profile: knowledge + lessons + plugins + safe settings; model/runtime and cloud secret are excluded.
- Cloud API secret: Windows Credential Manager only.

## Important source files

- `desktop/LocalAIOS/MainForm.cs`: complete chat workflow and user interface.
- `desktop/LocalAIOS/HardwareProfiler.cs`: RAM-based local model selection.
- `desktop/LocalAIOS/RuntimeManager.cs`: engine/model download and local server lifecycle.
- `desktop/LocalAIOS/LocalModelClient.cs`: local inference.
- `desktop/LocalAIOS/ReasoningRouter.cs`: task-aware fast/deep reasoning selection.
- `desktop/LocalAIOS/ConversationShortcut.cs`: safe instant answers that bypass model startup for trivial chat.
- `desktop/LocalAIOS/CloudCompute.cs`: free cloud route and routing policy.
- `desktop/LocalAIOS/InternetBrain.cs`: need detection, free search, page retrieval, and relevance extraction.
- `desktop/LocalAIOS/KnowledgeStore.cs`: persistent source map and expiring content cache.
- `desktop/LocalAIOS/LessonMemory.cs`: compact learning, recall, and forgetting.
- `desktop/LocalAIOS/PluginManager.cs`: plugin schema, matching, and installation.
- `desktop/LocalAIOS/CapabilityGapDetector.cs`: detects requests needing a reusable specialist ability.
- `desktop/LocalAIOS/CapabilityDevelopmentEngine.cs`: learns and installs portable source/workflow/validator recipes.
- `desktop/LocalAIOS/ProfileTransferService.cs`: cross-PC export/import/sync.
- `desktop/LocalAIOS/UpdateService.cs`: knowledge/app update feed.
- `desktop/LocalAIOS/SecretStore.cs`: Windows Credential Manager integration.
- `plugins/example.plugin.json`: plugin example.
- `updates/example-feed.json`: update-feed example.
- `src/` and `skills/`: earlier command-line prototype; not the primary product.

## Current request flow

```text
User message
  -> match an installed capability or detect a capability gap
  -> when missing, research and install a portable source/workflow/quality recipe
  -> recall compact source/lesson/plugin context
  -> decide whether fresh internet research is needed
  -> reacquire from saved source paths and fresh search; extract relevant sections
  -> select local model or configured free cloud compute
  -> generate a source-aware answer
  -> validate against capability quality rules and repair once if needed
  -> store compact sourced lesson when new sources were used
  -> prune/synchronize profile when configured
```

## Cross-PC continuation

The **Hafıza** UI exports/imports a `.laios` profile. The user may also select an already synchronized folder; the app then pulls a newer profile at startup and pushes changes after learning. The profile contains source paths, lessons, plugins, and safe configuration—not large model files or secrets.

## Known gaps / next work

1. Add source credibility scoring and explicit contradiction checks beyond current multi-source rules.
2. Add more interchangeable search, image and free-compute providers.
3. Add operating-system sandboxing beyond the current package/path/permission/timeout boundary for manually installed executable plugin tools.
4. Add automatic accelerator selection; current inference prioritizes the stable CPU path.
5. Host and sign the official shared update feed.
6. Benchmark quality, latency, memory use, retrieval accuracy and forgetting on representative home-user tasks.

## Build

```powershell
dotnet publish desktop/LocalAIOS/LocalAIOS.csproj -c Release -o release
```

No third-party .NET package is required. Do not edit `sources/`; it is read-only project reference material.
