# local-ai-os — mimari

Node tabanlı yerel AI orkestrasyonu ve C# masaüstü uygulaması.

## İşleyiş

Node CLI → orchestrator → skill/plugin/konfigürasyon bileşenleri; desktop/LocalAIOS ayrı .NET masaüstü katmanıdır.

## Kaynak ve sürüm ayrımı

`source/` altındaki ayrı kopyalar birleştirilmedi. `current`, `development`, `versions-and-development`, `archive-snapshots` ve `embedded-snapshots` mevcut olduğunda farklı dönemleri temsil eder. Klasör adı tek başına sürüm doğrulaması değildir; sürüm manifestleri esas alınır.

## Bileşen haritası

- [AppPaths.cs](source/current/desktop/LocalAIOS/AppPaths.cs)
- [AppSettings.cs](source/current/desktop/LocalAIOS/AppSettings.cs)
- [ArtifactService.cs](source/current/desktop/LocalAIOS/ArtifactService.cs)
- [CapabilityDevelopmentEngine.cs](source/current/desktop/LocalAIOS/CapabilityDevelopmentEngine.cs)
- [CapabilityGapDetector.cs](source/current/desktop/LocalAIOS/CapabilityGapDetector.cs)
- [CloudCompute.cs](source/current/desktop/LocalAIOS/CloudCompute.cs)
- [CloudSetupDialog.cs](source/current/desktop/LocalAIOS/CloudSetupDialog.cs)
- [ConversationShortcut.cs](source/current/desktop/LocalAIOS/ConversationShortcut.cs)
- [HardwareProfiler.cs](source/current/desktop/LocalAIOS/HardwareProfiler.cs)
- [ImageService.cs](source/current/desktop/LocalAIOS/ImageService.cs)
- [InternetBrain.cs](source/current/desktop/LocalAIOS/InternetBrain.cs)
- [KnowledgeStore.cs](source/current/desktop/LocalAIOS/KnowledgeStore.cs)
- [LessonMemory.cs](source/current/desktop/LocalAIOS/LessonMemory.cs)
- [LocalModelClient.cs](source/current/desktop/LocalAIOS/LocalModelClient.cs)
- [MainForm.cs](source/current/desktop/LocalAIOS/MainForm.cs)
- [PluginDialog.cs](source/current/desktop/LocalAIOS/PluginDialog.cs)
- [PluginManager.cs](source/current/desktop/LocalAIOS/PluginManager.cs)
- [PluginToolRunner.cs](source/current/desktop/LocalAIOS/PluginToolRunner.cs)
- [ProfileDialog.cs](source/current/desktop/LocalAIOS/ProfileDialog.cs)
- [ProfileTransferService.cs](source/current/desktop/LocalAIOS/ProfileTransferService.cs)
- [Program.cs](source/current/desktop/LocalAIOS/Program.cs)
- [ProjectAgentService.cs](source/current/desktop/LocalAIOS/ProjectAgentService.cs)
- [ProjectDialog.cs](source/current/desktop/LocalAIOS/ProjectDialog.cs)
- [ProjectRequestRouter.cs](source/current/desktop/LocalAIOS/ProjectRequestRouter.cs)
- [ProjectWorkspaceService.cs](source/current/desktop/LocalAIOS/ProjectWorkspaceService.cs)
- [PromptDialog.cs](source/current/desktop/LocalAIOS/PromptDialog.cs)
- [ReasoningModeDialog.cs](source/current/desktop/LocalAIOS/ReasoningModeDialog.cs)
- [ReasoningRouter.cs](source/current/desktop/LocalAIOS/ReasoningRouter.cs)
- [RuntimeManager.cs](source/current/desktop/LocalAIOS/RuntimeManager.cs)
- [SecretStore.cs](source/current/desktop/LocalAIOS/SecretStore.cs)
- [SelfTestRunner.cs](source/current/desktop/LocalAIOS/SelfTestRunner.cs)
- [UpdateBootstrap.cs](source/current/desktop/LocalAIOS/UpdateBootstrap.cs)
- [UpdateService.cs](source/current/desktop/LocalAIOS/UpdateService.cs)
- [cli.js](source/current/src/cli.js)
- [config.js](source/current/src/config.js)
- [memory-store.js](source/current/src/memory-store.js)
- [model-client.js](source/current/src/model-client.js)
- [orchestrator.js](source/current/src/orchestrator.js)
- [skill-registry.js](source/current/src/skill-registry.js)
- [task-contract.js](source/current/src/task-contract.js)
- [toolkit.js](source/current/src/toolkit.js)

## Teknik belgeler

- [AGENTS.md](source/current/AGENTS.md)
- [README.md](source/current/README.md)
- [PROJECT_CONTEXT.md](source/current/docs/PROJECT_CONTEXT.md)
- [VERIFICATION.md](source/current/release/VERIFICATION.md)
- [instructions.md](source/current/skills/software_ai/instructions.md)
