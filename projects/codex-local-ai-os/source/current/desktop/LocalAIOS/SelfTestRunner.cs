using System.Text.Json;
using System.IO.Compression;

namespace LocalAIOS;

internal sealed record SelfTestItem(string Name, bool Passed, string Detail, long DurationMs);

internal static class SelfTestRunner
{
    public static async Task<int> RunProjectSafetyAsync(string reportPath)
    {
        var testRoot = Path.Combine(Path.GetTempPath(), "LocalAIOS-project-safety-" + Guid.NewGuid().ToString("N"));
        try
        {
            var source = Path.Combine(testRoot, "General");
            Directory.CreateDirectory(source);
            await File.WriteAllTextAsync(Path.Combine(source, "app.txt"), "original");
            Directory.CreateDirectory(Path.Combine(source, "bin"));
            await File.WriteAllTextAsync(Path.Combine(source, "bin", "temporary.txt"), "skip");
            var clone = await ProjectWorkspaceService.CreateNextVersionAsync(source, CancellationToken.None);
            var result = await ProjectAgentService.ApplyPlanAsync(clone.ProjectPath, "uygulamayı geliştir",
                new ProjectChangePlan("v2 değişikliği", [new ProjectFileChange("app.txt", "version two")]), CancellationToken.None);
            var sourceUnchanged = await File.ReadAllTextAsync(Path.Combine(source, "app.txt")) == "original";
            var cloneChanged = await File.ReadAllTextAsync(Path.Combine(clone.ProjectPath, "app.txt")) == "version two";
            var cacheSkipped = !File.Exists(Path.Combine(clone.ProjectPath, "bin", "temporary.txt"));
            var markerExists = File.Exists(Path.Combine(clone.ProjectPath, ".localaios", "project.json"));
            var escapeBlocked = false;
            try { ProjectWorkspaceService.SafePath(clone.ProjectPath, "..\\source.txt"); }
            catch { escapeBlocked = true; }
            var passed = sourceUnchanged && cloneChanged && cacheSkipped && markerExists && escapeBlocked && result.Files.Length == 1;
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(reportPath))!);
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed,
                sourceUnchanged,
                cloneChanged,
                cacheSkipped,
                markerExists,
                escapeBlocked,
                cloneFolder = Path.GetFileName(clone.ProjectPath)
            }, AppSettings.JsonOptions));
            return passed ? 0 : 1;
        }
        catch (Exception exception)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(reportPath))!);
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed = false,
                error = exception.Message
            }, AppSettings.JsonOptions));
            return 1;
        }
        finally
        {
            try { if (Directory.Exists(testRoot)) Directory.Delete(testRoot, true); } catch { }
        }
    }

    public static async Task<int> RunPerformanceAsync(string reportPath)
    {
        using var cancellation = new CancellationTokenSource(TimeSpan.FromMinutes(2));
        var hardware = HardwareProfiler.Detect();
        using var runtime = new RuntimeManager(11435, hardware.Model);
        var progress = new DirectProgress(_ => { });
        try
        {
            await runtime.EnsureInstalledAsync(progress, cancellation.Token);
            await runtime.StartAsync(progress, cancellation.Token);
            var started = Environment.TickCount64;
            var answer = await new LocalModelClient(11435).ChatAsync(
                [new ChatMessage("user", "selam")], "", false, cancellation.Token);
            var duration = Environment.TickCount64 - started;
            var routingPassed = !ReasoningRouter.ShouldThinkDeeply("selam", "balanced") &&
                ReasoningRouter.ShouldThinkDeeply("Bu karmaşık mimariyi derin düşün ve risk analizi yap", "balanced") &&
                !ReasoningRouter.ShouldThinkDeeply("karmaşık mimari", "fast") &&
                ReasoningRouter.ShouldThinkDeeply("selam", "powerful");
            var shortcutPassed = ConversationShortcut.TryAnswer("selam", out var shortcut) &&
                shortcut.Contains("Selam", StringComparison.OrdinalIgnoreCase);
            var researchStarted = Environment.TickCount64;
            var research = await new InternetBrain().ResearchAsync("Qwen3 official model information", cancellation.Token);
            var researchDuration = Environment.TickCount64 - researchStarted;
            var researchPassed = research.Sources.Length >= 2 && researchDuration < 30000;
            var passed = !string.IsNullOrWhiteSpace(answer) && duration < 30000 && routingPassed &&
                shortcutPassed && researchPassed;
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed,
                model = hardware.Model.DisplayName,
                greetingAnswer = answer,
                greetingDurationMs = duration,
                reasoningModeRouting = routingPassed,
                instantGreetingShortcut = shortcutPassed,
                parallelInternetResearchMs = researchDuration,
                parallelInternetSources = research.Sources.Length
            }, AppSettings.JsonOptions), cancellation.Token);
            return passed ? 0 : 1;
        }
        catch (Exception exception)
        {
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed = false,
                error = exception.Message
            }, AppSettings.JsonOptions));
            return 1;
        }
    }

    public static async Task<int> RunImageAsync(string reportPath)
    {
        try
        {
            var file = await new ImageService().GenerateAsync(
                "minimal blue robot icon on white background", 256, CancellationToken.None);
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed = true,
                test = "Image generation repair",
                output = file,
                bytes = new FileInfo(file).Length
            }, AppSettings.JsonOptions));
            return 0;
        }
        catch (Exception exception)
        {
            await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
            {
                completedAt = DateTimeOffset.Now,
                passed = false,
                test = "Image generation repair",
                error = exception.Message
            }, AppSettings.JsonOptions));
            return 1;
        }
    }

    public static async Task<int> RunAsync(string reportPath)
    {
        var progressPath = reportPath + ".progress.log";
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(reportPath))!);
        File.WriteAllText(progressPath, "Self-test started\n");
        var results = new List<SelfTestItem>();
        var hardware = HardwareProfiler.Detect();
        using var runtime = new RuntimeManager(11435, hardware.Model);
        var model = new LocalModelClient(11435);

        await Run("Local engine and model setup", async () =>
        {
            var progress = new DirectProgress(item => File.AppendAllText(progressPath, $"{DateTime.Now:T} {item.Message} {item.Percent}%\n"));
            await runtime.EnsureInstalledAsync(progress, CancellationToken.None);
            await runtime.StartAsync(progress, CancellationToken.None);
            return hardware.Model.DisplayName;
        });

        await Run("Real local chat", async () =>
        {
            var answer = await model.GenerateAsync(
                "Answer accurately and very briefly in Turkish.",
                "Türkiye'nin başkenti nedir? Yalnızca şehir adını yaz.", CancellationToken.None);
            if (!answer.Contains("Ankara", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Beklenen Ankara cevabı alınamadı: " + answer);
            return answer;
        });

        InternetResearch? research = null;
        await Run("Live internet research", async () =>
        {
            research = await new InternetBrain().ResearchAsync("Qwen3 official model information", CancellationToken.None);
            if (research.Sources.Length < 2 || research.Context.Length < 300)
                throw new InvalidOperationException("Yeterli internet kaynağı alınamadı.");
            return $"{research.Sources.Length} sources";
        });

        await Run("Learn and recall sourced lesson", async () =>
        {
            var memory = new LessonMemory();
            await memory.LearnAsync("Self-test Qwen3 bilgisi", "Qwen3 hakkında kaynaklı test dersi.", research?.Sources ?? [], CancellationToken.None);
            var recalled = await memory.RecallAsync("Self-test Qwen3 bilgisi", CancellationToken.None);
            if (!recalled.Contains("kaynaklı test", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Ders geri çağrılamadı.");
            return "Lesson stored with sources and method";
        });

        await Run("Capability acquisition, storage and routing", async () =>
        {
            var manager = new PluginManager();
            var capability = await new CapabilityDevelopmentEngine(manager, new InternetBrain()).AcquireAsync(
                "teknik SEO denetimi", model, CancellationToken.None);
            var context = PluginManager.BuildContext([capability]);
            if (capability.Sources.Length < 2 || capability.Workflow.Length < 4 ||
                !context.Contains("Bilgiye erişim yolları", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Taşınabilir yetenek tarifi eksik üretildi.");
            var semanticRoute = await CapabilityGapDetector.AnalyzeAsync(
                "Web sitemin arama motorlarındaki teknik sağlığını incele", manager, model, CancellationToken.None);
            if (semanticRoute.Missing || semanticRoute.SelectedIds.Length == 0)
                throw new InvalidOperationException("Yetenek farklı ifadeyle anlamsal olarak eşleşmedi.");
            return $"{capability.Name}: {capability.Sources.Length} source paths, {capability.Workflow.Length} steps, semantic route passed";
        });

        await Run("Portable cross-PC profile", async () =>
        {
            var file = Path.Combine(AppPaths.Root, "self-test-profile.laios");
            await new ProfileTransferService(new AppSettings()).ExportAsync(file, CancellationToken.None);
            bool capabilityIncluded;
            using (var archive = ZipFile.OpenRead(file))
                capabilityIncluded = archive.Entries.Any(entry =>
                    entry.FullName.StartsWith("plugins/", StringComparison.OrdinalIgnoreCase) &&
                    entry.FullName.EndsWith("manifest.json", StringComparison.OrdinalIgnoreCase));
            if (!capabilityIncluded) throw new InvalidOperationException("Edinilen yetenek profile eklenmedi.");
            File.Delete(file);
            return "Capability source routes and workflows included";
        });

        await Run("Mini application generation", async () =>
        {
            var file = await new ArtifactService().CreateMiniAppAsync(
                "Türkçe arayüzlü, iki sayıyı toplayan basit mini uygulama oluştur.", model, CancellationToken.None);
            var html = await File.ReadAllTextAsync(file);
            if (!html.Contains("<html", StringComparison.OrdinalIgnoreCase) || !html.Contains("script", StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Mini uygulama geçerli değil.");
            return file;
        });

        await Run("Image generation", async () =>
        {
            var file = await new ImageService().GenerateAsync("minimal blue robot icon on white background", 256, CancellationToken.None);
            return $"{file} ({new FileInfo(file).Length} bytes)";
        });

        var passed = results.All(item => item.Passed);
        await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(new
        {
            completedAt = DateTimeOffset.Now,
            passed,
            hardware = new { hardware.RamGb, hardware.LogicalProcessors },
            model = hardware.Model.DisplayName,
            tests = results
        }, AppSettings.JsonOptions));
        File.AppendAllText(progressPath, passed ? "SELF_TEST_PASSED\n" : "SELF_TEST_FAILED\n");
        return passed ? 0 : 1;

        async Task Run(string name, Func<Task<string>> test)
        {
            var started = Environment.TickCount64;
            File.AppendAllText(progressPath, $"RUN {name}\n");
            try
            {
                var detail = await test();
                results.Add(new(name, true, detail, Environment.TickCount64 - started));
                File.AppendAllText(progressPath, $"PASS {name}\n");
            }
            catch (Exception exception)
            {
                results.Add(new(name, false, exception.Message, Environment.TickCount64 - started));
                File.AppendAllText(progressPath, $"FAIL {name}: {exception.Message}\n");
            }
        }
    }

    private sealed class DirectProgress(Action<SetupProgress> action) : IProgress<SetupProgress>
    {
        public void Report(SetupProgress value) => action(value);
    }
}
