using System.Diagnostics;
using System.Text.RegularExpressions;

namespace LocalAIOS;

internal sealed class MainForm : Form
{
    private readonly RichTextBox _chat = new();
    private readonly TextBox _input = new();
    private readonly Button _send = new();
    private readonly Button _prepare = new();
    private readonly Button _addKnowledge = new();
    private readonly Button _updates = new();
    private readonly Button _cloud = new();
    private readonly Button _plugins = new();
    private readonly Button _profile = new();
    private readonly Button _image = new();
    private readonly Button _mode = new();
    private readonly Button _project = new();
    private readonly Label _status = new();
    private readonly ProgressBar _progress = new();
    private readonly AppSettings _settings = AppSettings.Load();
    private readonly KnowledgeStore _knowledge = new();
    private readonly PluginManager _pluginManager = new();
    private readonly InternetBrain _internet = new();
    private readonly LessonMemory _lessons = new();
    private readonly List<ChatMessage> _history = [];
    private readonly CancellationTokenSource _lifetime = new();
    private RuntimeManager? _runtime;
    private LocalModelClient? _model;
    private HardwareProfile? _hardware;
    private CancellationTokenSource? _activeRequest;
    private bool _stoppedByUser;
    private bool _busy;

    public MainForm()
    {
        Text = "Local AI OS";
        MinimumSize = new Size(1180, 620);
        Size = new Size(1320, 760);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = Color.FromArgb(17, 19, 24);
        ForeColor = Color.White;
        Font = new Font("Segoe UI", 10);
        BuildInterface();
        Shown += OnShown;
        FormClosing += (_, _) => { _lifetime.Cancel(); _runtime?.Dispose(); };
    }

    private void BuildInterface()
    {
        var header = new Panel { Dock = DockStyle.Top, Height = 72, BackColor = Color.FromArgb(24, 27, 34) };
        var title = new Label { Text = "LOCAL AI OS", Font = new Font("Segoe UI Semibold", 15), Left = 22, Top = 13, AutoSize = true };
        _status.SetBounds(24, 43, 300, 20);
        _status.Text = "Başlatılıyor…";
        _status.ForeColor = Color.FromArgb(154, 163, 180);

        ConfigureButton(_prepare, "Yapay zekâyı hazırla", 165);
        _prepare.Click += async (_, _) => await PrepareAsync();
        ConfigureButton(_cloud, "Online güç", 105);
        _cloud.Click += (_, _) => ConfigureCloud();
        ConfigureButton(_mode, $"Mod: {ReasoningRouter.Label(_settings.ReasoningMode)}", 120);
        _mode.Click += (_, _) => ConfigureReasoningMode();
        ConfigureButton(_plugins, "Eklentiler", 95);
        _plugins.Click += async (_, _) =>
        {
            new PluginDialog(_pluginManager).ShowDialog(this);
            await SyncProfileAsync();
        };
        ConfigureButton(_profile, "Hafıza", 90);
        _profile.Click += (_, _) => new ProfileDialog(_settings).ShowDialog(this);
        ConfigureButton(_image, "Görsel", 85);
        _image.Click += async (_, _) => await GenerateImageAsync();
        ConfigureButton(_updates, "Güncellemeler", 110);
        _updates.Click += async (_, _) => await CheckUpdatesAsync(true);
        ConfigureButton(_addKnowledge, "Bilgi ekle", 95);
        _addKnowledge.Click += async (_, _) => await AddKnowledgeAsync();
        ConfigureButton(_project, Directory.Exists(_settings.ActiveProjectPath) ? "Proje ✓" : "Proje", 85);
        _project.Click += async (_, _) => await ConfigureProjectAsync();
        var actions = new FlowLayoutPanel
        {
            Dock = DockStyle.Right,
            Width = 1035,
            Padding = new Padding(8, 17, 8, 0),
            FlowDirection = FlowDirection.RightToLeft,
            WrapContents = false
        };
        actions.Controls.AddRange([_addKnowledge, _updates, _profile, _plugins, _image, _cloud, _mode, _project, _prepare]);
        header.Controls.AddRange([title, _status, actions]);

        _chat.Dock = DockStyle.Fill;
        _chat.ReadOnly = true;
        _chat.BorderStyle = BorderStyle.None;
        _chat.BackColor = Color.FromArgb(17, 19, 24);
        _chat.ForeColor = Color.FromArgb(232, 234, 240);
        _chat.Font = new Font("Segoe UI", 11);
        _chat.DetectUrls = true;
        _chat.LinkClicked += (_, eventArgs) =>
        {
            if (!string.IsNullOrWhiteSpace(eventArgs.LinkText))
                Process.Start(new ProcessStartInfo(eventArgs.LinkText) { UseShellExecute = true });
        };

        var footer = new Panel { Dock = DockStyle.Bottom, Height = 145, Padding = new Padding(20), BackColor = Color.FromArgb(24, 27, 34) };
        _input.Multiline = true;
        _input.ScrollBars = ScrollBars.Vertical;
        _input.Dock = DockStyle.Fill;
        _input.Margin = new Padding(0, 0, 10, 12);
        _input.BackColor = Color.FromArgb(34, 38, 47);
        _input.ForeColor = Color.White;
        _input.BorderStyle = BorderStyle.FixedSingle;
        _input.KeyDown += async (_, eventArgs) =>
        {
            if (eventArgs.KeyCode == Keys.Enter && !eventArgs.Shift)
            {
                eventArgs.SuppressKeyPress = true;
                await SendAsync();
            }
        };
        _send.Text = "Gönder";
        _send.Dock = DockStyle.Fill;
        _send.Margin = new Padding(0, 0, 0, 12);
        _send.BackColor = Color.FromArgb(90, 105, 255);
        _send.ForeColor = Color.White;
        _send.FlatStyle = FlatStyle.Flat;
        _send.Click += async (_, _) =>
        {
            if (_busy) { StopActiveRequest(); return; }
            await SendAsync();
        };
        _progress.Dock = DockStyle.Bottom;
        _progress.Height = 8;
        _progress.Visible = false;
        var composer = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1, Margin = Padding.Empty };
        composer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        composer.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 130));
        composer.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        composer.Controls.Add(_input, 0, 0);
        composer.Controls.Add(_send, 1, 0);
        footer.Controls.Add(composer);
        footer.Controls.Add(_progress);

        Controls.Add(_chat);
        Controls.Add(footer);
        Controls.Add(header);
    }

    private static void ConfigureButton(Button button, string text, int width)
    {
        button.Text = text;
        button.Size = new Size(width, 36);
    }

    private async void OnShown(object? sender, EventArgs eventArgs)
    {
        try { await new ProfileTransferService(_settings).PullAsync(_lifetime.Token); } catch { }
        _hardware = HardwareProfiler.Detect();
        _runtime = new RuntimeManager(_settings.ServerPort, _hardware.Model);
        _model = new LocalModelClient(_settings.ServerPort);
        await _lessons.PruneAsync(_lifetime.Token);
        await _knowledge.PruneAsync(_lifetime.Token);
        if (_runtime.IsInstalled)
            await StartModelAsync();
        else
        {
            Append("Sistem", $"Bu bilgisayar için {_hardware.Model.DisplayName} seçildi. İlk kullanımda {_hardware.Model.DownloadSize} model indirilecek. Sonrasında internet olmadan çalışır.");
            SetReady(false, "Kurulum gerekli");
        }
        await CheckUpdatesAsync(false);
    }

    private async Task PrepareAsync()
    {
        if (_runtime is null || _busy) return;
        if (!_runtime.IsInstalled && MessageBox.Show(
            $"Bu bilgisayar için {_runtime.Model.DisplayName} seçildi. Yerel motor ve {_runtime.Model.DownloadSize} model indirilecek. Devam edilsin mi?",
            "Yapay zekâyı hazırla", MessageBoxButtons.YesNo, MessageBoxIcon.Information) != DialogResult.Yes) return;
        await RunBusyAsync(async () =>
        {
            var progress = UiProgress();
            await _runtime.EnsureInstalledAsync(progress, _lifetime.Token);
            await _runtime.StartAsync(progress, _lifetime.Token);
            Append("Sistem", "Yapay zekân hazır. İstediğin konuda konuşabilir veya bir bilgi bağlantısı verebilirsin.");
            SetReady(true, "Hazır · tamamen yerel");
        });
    }

    private async Task StartModelAsync()
    {
        if (_runtime is null) return;
        await RunBusyAsync(async () =>
        {
            await _runtime.StartAsync(UiProgress(), _lifetime.Token);
            SetReady(true, "Hazır · tamamen yerel");
        });
    }

    private async Task SendAsync()
    {
        var text = _input.Text.Trim();
        if (_busy || string.IsNullOrWhiteSpace(text)) return;
        if (_runtime is null || !_runtime.IsInstalled)
        {
            MessageBox.Show("Önce ‘Yapay zekâyı hazırla’ düğmesine basın.", "Local AI OS");
            return;
        }
        var url = Regex.Match(text, @"https?://\S+", RegexOptions.IgnoreCase).Value.TrimEnd('.', ',', ')');
        if (!string.IsNullOrEmpty(url) && MessageBox.Show(
            "Bu bağlantıyı bilgi kaynaklarıma eklememi ister misin?",
            "Yeni bilgi kaynağı", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
        {
            await IngestUrlAsync(url);
        }

        _input.Clear();
        Append("Sen", text);
        _history.Add(new("user", text));
        using var requestCancellation = CancellationTokenSource.CreateLinkedTokenSource(_lifetime.Token);
        _activeRequest = requestCancellation;
        _stoppedByUser = false;
        _send.Text = "Durdur";
        try
        {
        await RunBusyAsync(async () =>
        {
            if (ProjectRequestRouter.IsContinuationRequest(text))
            {
                var clone = await SelectAndCloneProjectAsync(requestCancellation.Token);
                if (clone is null)
                {
                    SetReady(true, $"Hazır · {ReasoningRouter.Label(_settings.ReasoningMode)}");
                    return;
                }
                var projectMessage = $"Eski proje değişmeden bırakıldı. {clone.CopiedFiles} kaynak dosya yeni çalışma kopyasına alındı. Bundan sonraki değişiklikleri yalnız burada yapacağım:\n{clone.ProjectPath}";
                _history.Add(new("assistant", projectMessage));
                Append("Local AI", projectMessage);
                SetReady(true, "Yeni proje kopyası hazır");
                return;
            }
            if (Directory.Exists(_settings.ActiveProjectPath) && ProjectRequestRouter.IsChangeRequest(text))
            {
                _status.Text = $"{Path.GetFileName(_settings.ActiveProjectPath)} üzerinde çalışılıyor…";
                var result = await new ProjectAgentService(_model!).ApplyAsync(
                    _settings.ActiveProjectPath, text, requestCancellation.Token);
                var files = result.Files.Length == 0 ? "Dosya değişikliği gerekmedi." :
                    $"Değiştirilen dosyalar: {string.Join(", ", result.Files)}";
                var projectMessage = $"{result.Summary}\n{files}\nÇalışma klasörü: {result.ProjectPath}";
                _history.Add(new("assistant", projectMessage));
                Append("Local AI", projectMessage);
                SetReady(true, "Proje güncellendi");
                return;
            }
            if (IsMiniAppRequest(text))
            {
                _status.Text = "Mini uygulama oluşturuluyor…";
                var file = await new ArtifactService().CreateMiniAppAsync(text, _model!, requestCancellation.Token);
                var artifactMessage = $"Mini uygulama oluşturuldu: {new Uri(file).AbsoluteUri}";
                _history.Add(new("assistant", artifactMessage));
                Append("Local AI", artifactMessage);
                Process.Start(new ProcessStartInfo(file) { UseShellExecute = true });
                SetReady(true, "Mini uygulama hazır");
                return;
            }
            if (IsImageRequest(text))
            {
                _status.Text = "Görsel oluşturuluyor…";
                var file = await new ImageService().GenerateAsync(text, 768, requestCancellation.Token);
                var imageMessage = $"Görsel oluşturuldu: {new Uri(file).AbsoluteUri}";
                _history.Add(new("assistant", imageMessage));
                Append("Local AI", imageMessage);
                ShowImage(file);
                SetReady(true, "Görsel hazır");
                return;
            }
            if (ConversationShortcut.TryAnswer(text, out var shortcutAnswer))
            {
                _history.Add(new("assistant", shortcutAnswer));
                Append("Local AI", shortcutAnswer);
                SetReady(true, $"Hazır · {ReasoningRouter.Label(_settings.ReasoningMode)}");
                return;
            }
            PluginManifest? acquired = null;
            var gap = await CapabilityGapDetector.AnalyzeAsync(text, _pluginManager, _model!, requestCancellation.Token);
            if (gap.Missing)
            {
                _status.Text = "Eksik yetenek internetten ediniliyor…";
                acquired = await new CapabilityDevelopmentEngine(_pluginManager, _internet)
                    .AcquireAsync(string.IsNullOrWhiteSpace(gap.Need) ? text : gap.Need, _model!, requestCancellation.Token,
                        string.IsNullOrWhiteSpace(url) ? [] : [url]);
                Append("Sistem", $"“{acquired.Name}” yeteneği edinildi. Kaynak yolları, uygulama yöntemi ve kalite kontrolleri profilinde saklandı.");
                await SyncProfileAsync();
            }
            var deepThinking = ReasoningRouter.ShouldThinkDeeply(text, _settings.ReasoningMode);
            _status.Text = deepThinking ? "Derin düşünüyor…" : "Hızlı düşünüyor…";
            var projectTask = Directory.Exists(_settings.ActiveProjectPath) && ProjectRequestRouter.IsProjectRelated(text);
            var projectContext = projectTask
                ? await ProjectWorkspaceService.BuildContextAsync(_settings.ActiveProjectPath, text, requestCancellation.Token)
                : "";
            var knowledge = await _knowledge.SearchAsync(text, requestCancellation.Token);
            var lessons = await _lessons.RecallAsync(text, requestCancellation.Token);
            var availablePlugins = _pluginManager.List();
            var selectedIds = gap.SelectedIds ?? [];
            var matchedPlugins = acquired is not null ? new[] { acquired } : availablePlugins
                .Where(plugin => selectedIds.Contains(plugin.Id, StringComparer.OrdinalIgnoreCase)).Take(3).ToArray();
            var pluginContext = PluginManager.BuildContext(matchedPlugins);
            var toolContext = await PluginToolRunner.RunAsync(matchedPlugins, text, requestCancellation.Token);
            var research = new InternetResearch("", []);
            if (matchedPlugins.Length > 0 || InternetBrain.ShouldResearch(text,
                    !string.IsNullOrWhiteSpace(knowledge.Content) || !string.IsNullOrWhiteSpace(lessons)))
            {
                _status.Text = "İnternetten gerekli bilgi bulunuyor…";
                try
                {
                    research = await _internet.ResearchAsync(text,
                        matchedPlugins.SelectMany(plugin => plugin.Sources).Select(source => source.Url), requestCancellation.Token);
                }
                catch { }
            }
            var context = string.Join("\n\n", new[] { projectContext, knowledge.Content, lessons, pluginContext, toolContext, research.Context }
                .Where(value => !string.IsNullOrWhiteSpace(value)));
            var useCloud = _hardware is not null && ComputeRouter.ShouldUseCloud(text, projectTask, _hardware, _settings);
            var cloudKey = useCloud ? SecretStore.Read() : null;
            string answer;
            if (useCloud && cloudKey is not null)
            {
                _status.Text = "Ücretsiz çevrimiçi güç kullanılıyor…";
                answer = await new CloudComputeClient(cloudKey).ChatAsync(_history, context, requestCancellation.Token);
            }
            else
            {
                answer = await _model!.ChatAsync(_history, context, deepThinking, requestCancellation.Token);
            }
            var usedSources = knowledge.Sources.Concat(research.Sources).Distinct().ToArray();
            var qualityFailures = _pluginManager.ValidateAnswer(answer, usedSources, matchedPlugins);
            if (qualityFailures.Length > 0)
            {
                _status.Text = "Sonuç kalite kontrolünden geçiriliyor…";
                answer = await _model!.GenerateAsync("""
                    Improve the draft so every stated quality failure is fixed. Use only the supplied source
                    context for factual claims, never invent sources, and include used URLs under Kaynaklar.
                    Return only the improved answer in the user's language.
                    """, $"İstek:\n{text}\n\nTaslak:\n{answer}\n\nEksikler:\n{string.Join("\n", qualityFailures)}\n\nKaynak bağlamı:\n{context}", requestCancellation.Token);
            }
            _history.Add(new("assistant", answer));
            var applicationMethod = matchedPlugins.Length == 0 ? null : string.Join(" → ", matchedPlugins
                .SelectMany(plugin => plugin.Workflow).Select(step => $"{step.Action}: {step.Instruction}"));
            await _lessons.LearnAsync(text, answer, usedSources, requestCancellation.Token, applicationMethod);
            await SyncProfileAsync();
            Append("Local AI", answer);
            SetReady(true, useCloud ? "Hazır · hibrit" : $"Hazır · {ReasoningRouter.Label(_settings.ReasoningMode)}");
        });
        }
        finally
        {
            _activeRequest = null;
            _send.Text = "Gönder";
        }
    }

    private void StopActiveRequest()
    {
        if (_activeRequest is null) return;
        _stoppedByUser = true;
        _status.Text = "Durduruluyor…";
        _activeRequest.Cancel();
    }

    private void ConfigureReasoningMode()
    {
        using var dialog = new ReasoningModeDialog(_settings.ReasoningMode);
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        _settings.ReasoningMode = dialog.SelectedMode;
        _settings.Save();
        _mode.Text = $"Mod: {ReasoningRouter.Label(_settings.ReasoningMode)}";
        Append("Sistem", $"Zekâ modu {ReasoningRouter.Label(_settings.ReasoningMode)} olarak ayarlandı.");
    }

    private async Task AddKnowledgeAsync()
    {
        using var dialog = new PromptDialog("Bilgi kaynağı ekle", "Öğrenilecek web sayfasının bağlantısı:");
        if (dialog.ShowDialog(this) == DialogResult.OK && !string.IsNullOrWhiteSpace(dialog.Value))
            await IngestUrlAsync(dialog.Value);
    }

    private async Task IngestUrlAsync(string url)
    {
        await RunBusyAsync(async () =>
        {
            _status.Text = "Kaynağın yolu öğreniliyor…";
            var document = await _knowledge.AddUrlAsync(url, _lifetime.Token);
            await SyncProfileAsync();
            Append("Sistem", $"“{document.Title}” bilgi kaynaklarıma eklendi. Gerektiğinde bu kaynaktan güncel bilgiyi yeniden alacağım.");
            SetReady(_runtime?.IsInstalled == true, "Bilgi kaynağı eklendi");
        });
    }

    private void ConfigureCloud()
    {
        using var dialog = new CloudSetupDialog(_settings);
        if (dialog.ShowDialog(this) == DialogResult.OK)
            Append("Sistem", _settings.CloudEnabled
                ? "Ücretsiz çevrimiçi güç gerektiğinde otomatik kullanılacak."
                : "Çevrimiçi güç kapatıldı; yalnız yerel model kullanılacak.");
    }

    private async Task ConfigureProjectAsync()
    {
        if (_busy) return;
        using var dialog = new ProjectDialog(_settings.ActiveProjectPath);
        if (dialog.ShowDialog(this) != DialogResult.OK || !dialog.CreateCopyRequested) return;
        await RunBusyAsync(async () =>
        {
            var clone = await SelectAndCloneProjectAsync(_lifetime.Token);
            if (clone is null) return;
            Append("Sistem", $"Eski proje değiştirilmedi. Yeni çalışma kopyası hazır:\n{clone.ProjectPath}");
            SetReady(_runtime?.IsInstalled == true, "Yeni proje kopyası hazır");
        });
    }

    private async Task<ProjectCloneResult?> SelectAndCloneProjectAsync(CancellationToken cancellationToken)
    {
        using var picker = new FolderBrowserDialog
        {
            Description = "Kaldığınız eski proje klasörünü seçin. Bu klasör yalnızca okunacak.",
            UseDescriptionForTitle = true,
            ShowNewFolderButton = false
        };
        if (picker.ShowDialog(this) != DialogResult.OK || string.IsNullOrWhiteSpace(picker.SelectedPath)) return null;
        if (MessageBox.Show(
            "Seçtiğiniz eski klasörde hiçbir şey değiştirilmeyecek. Yanında yeni bir v2 çalışma klasörü oluşturulsun mu?",
            "Yeni sürümde devam et", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return null;
        _status.Text = "Eski proje okunuyor, güvenli çalışma kopyası hazırlanıyor…";
        var clone = await ProjectWorkspaceService.CreateNextVersionAsync(picker.SelectedPath, cancellationToken);
        _settings.ActiveProjectSourcePath = clone.SourcePath;
        _settings.ActiveProjectPath = clone.ProjectPath;
        _settings.Save();
        _project.Text = "Proje ✓";
        return clone;
    }

    private async Task GenerateImageAsync()
    {
        using var dialog = new PromptDialog("Görsel oluştur", "Nasıl bir görsel istediğini yaz:");
        if (dialog.ShowDialog(this) != DialogResult.OK || string.IsNullOrWhiteSpace(dialog.Value)) return;
        await RunBusyAsync(async () =>
        {
            _status.Text = "Görsel oluşturuluyor…";
            var file = await new ImageService().GenerateAsync(dialog.Value, 768, _lifetime.Token);
            Append("Local AI", $"Görsel oluşturuldu: {new Uri(file).AbsoluteUri}");
            ShowImage(file);
            SetReady(_runtime?.IsInstalled == true, "Görsel hazır");
        });
    }

    private async Task CheckUpdatesAsync(bool interactive)
    {
        if (_busy) return;
        if (string.IsNullOrWhiteSpace(_settings.UpdateFeedUrl))
        {
            if (!interactive) return;
            using var dialog = new PromptDialog("Güncelleme kaynağı", "Ortak güncelleme bağlantısını girin:", _settings.UpdateFeedUrl);
            if (dialog.ShowDialog(this) != DialogResult.OK || string.IsNullOrWhiteSpace(dialog.Value)) return;
            _settings.UpdateFeedUrl = dialog.Value;
            _settings.Save();
        }
        try
        {
            var service = new UpdateService(_settings);
            var update = await service.CheckAsync(_lifetime.Token);
            var appUpdate = update is not null && UpdateService.HasAppUpdate(update.Value.Feed);
            if (update is null || (update.Value.NewPacks.Length == 0 && !appUpdate))
            {
                if (interactive) MessageBox.Show("Yeni bilgi veya özellik güncellemesi yok.", "Güncellemeler");
                return;
            }
            var parts = update.Value.NewPacks.Select(pack => $"• {pack.Title}\n  {pack.Summary}").ToList();
            if (appUpdate) parts.Insert(0, $"• Yeni uygulama sürümü {update.Value.Feed.AppVersion}\n  {update.Value.Feed.Notes}");
            if (MessageBox.Show($"Yeni güncellemeler bulundu:\n\n{string.Join("\n\n", parts)}\n\nŞimdi yüklensin mi?",
                "Local AI OS güncellemesi", MessageBoxButtons.YesNo, MessageBoxIcon.Information) != DialogResult.Yes) return;
            await RunBusyAsync(async () =>
            {
                _status.Text = "Güncellemeler yükleniyor…";
                await service.InstallPacksAsync(update.Value.NewPacks, _lifetime.Token);
                await SyncProfileAsync();
                Append("Sistem", "Yeni bilgi paketleri yüklendi.");
                if (appUpdate)
                {
                    var updater = await service.DownloadAppUpdateAsync(update.Value.Feed, _lifetime.Token);
                    var current = Environment.ProcessPath ?? throw new InvalidOperationException("Uygulama yolu bulunamadı.");
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = updater,
                        UseShellExecute = true,
                        Arguments = $"--apply-update \"{current}\" {Environment.ProcessId}"
                    });
                    BeginInvoke(Application.Exit);
                }
            });
        }
        catch (Exception exception)
        {
            if (interactive) MessageBox.Show(exception.Message, "Güncelleme alınamadı", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private Progress<SetupProgress> UiProgress() => new(progress =>
    {
        _status.Text = progress.Message;
        _progress.Visible = progress.Percent is > 0 and < 100;
        _progress.Value = Math.Clamp(progress.Percent, 0, 100);
    });

    private async Task RunBusyAsync(Func<Task> action)
    {
        _busy = true;
        SetActions(false);
        try { await action(); }
        catch (OperationCanceledException)
        {
            if (_stoppedByUser)
            {
                Append("Sistem", "İşlem durduruldu.");
                SetReady(_runtime?.IsInstalled == true, "Durduruldu");
            }
        }
        catch (Exception exception)
        {
            Append("Sistem", $"İşlem tamamlanamadı: {exception.Message}");
            _status.Text = "Bir sorun oluştu";
        }
        finally
        {
            _busy = false;
            _progress.Visible = false;
            SetActions(true);
        }
    }

    private void SetActions(bool enabled)
    {
        _send.Enabled = true;
        _input.Enabled = enabled;
        _prepare.Enabled = _addKnowledge.Enabled = _updates.Enabled = _cloud.Enabled = _plugins.Enabled =
            _profile.Enabled = _image.Enabled = _mode.Enabled = _project.Enabled = enabled;
    }

    private async Task SyncProfileAsync()
    {
        try { await new ProfileTransferService(_settings).PushAsync(_lifetime.Token); }
        catch { }
    }

    private void SetReady(bool ready, string status)
    {
        _status.Text = status;
        _status.ForeColor = ready ? Color.FromArgb(94, 214, 140) : Color.FromArgb(245, 184, 84);
        _prepare.Visible = !ready;
    }

    private void Append(string speaker, string text)
    {
        _chat.SelectionStart = _chat.TextLength;
        _chat.SelectionFont = new Font(_chat.Font, FontStyle.Bold);
        _chat.SelectionColor = speaker == "Local AI" ? Color.FromArgb(133, 148, 255) : Color.FromArgb(198, 204, 218);
        _chat.AppendText($"{speaker}\n");
        _chat.SelectionFont = _chat.Font;
        _chat.SelectionColor = _chat.ForeColor;
        _chat.AppendText($"{text}\n\n");
        _chat.ScrollToCaret();
    }

    private static bool IsMiniAppRequest(string text) =>
        text.Contains("mini uygulama", StringComparison.OrdinalIgnoreCase) ||
        text.Contains("html uygulama", StringComparison.OrdinalIgnoreCase) ||
        text.Contains("web uygulaması oluştur", StringComparison.OrdinalIgnoreCase);

    private static bool IsImageRequest(string text) =>
        text.Contains("görsel oluştur", StringComparison.OrdinalIgnoreCase) ||
        text.Contains("resim oluştur", StringComparison.OrdinalIgnoreCase) ||
        text.Contains("görsel üret", StringComparison.OrdinalIgnoreCase) ||
        text.Contains("resim üret", StringComparison.OrdinalIgnoreCase);

    private void ShowImage(string file)
    {
        var window = new Form
        {
            Text = "Oluşturulan görsel",
            Size = new Size(820, 820),
            StartPosition = FormStartPosition.CenterParent,
            BackColor = Color.FromArgb(17, 19, 24)
        };
        window.Controls.Add(new PictureBox
        {
            Dock = DockStyle.Fill,
            SizeMode = PictureBoxSizeMode.Zoom,
            Image = Image.FromFile(file)
        });
        window.Show(this);
    }
}
