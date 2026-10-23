using System.Text.Json;
using System.Text.RegularExpressions;

namespace LocalAIOS;

internal sealed record LearnedLesson(
    string Question,
    string Lesson,
    string[] Sources,
    string LearningMethod,
    string LearnedAt,
    string LastUsedAt,
    int UseCount);

internal sealed class LessonMemory
{
    private static readonly Regex Words = new("[\\p{L}\\p{N}]{3,}", RegexOptions.Compiled);
    private static string FilePath => Path.Combine(AppPaths.Root, "memory", "lessons.json");

    public async Task<string> RecallAsync(string request, CancellationToken cancellationToken)
    {
        var lessons = await LoadAsync(cancellationToken);
        var terms = Tokenize(request);
        var selected = lessons.Select((lesson, index) => new
            {
                Lesson = lesson,
                Index = index,
                Score = terms.Count(term => $"{lesson.Question} {lesson.Lesson}".Contains(term, StringComparison.OrdinalIgnoreCase))
            })
            .Where(item => item.Score > 0).OrderByDescending(item => item.Score).Take(4).ToArray();
        if (selected.Length == 0) return "";
        var now = DateTimeOffset.UtcNow.ToString("O");
        foreach (var item in selected)
            lessons[item.Index] = item.Lesson with { LastUsedAt = now, UseCount = item.Lesson.UseCount + 1 };
        await SaveAsync(lessons, cancellationToken);
        return string.Join("\n", selected.Select(item =>
            $"- Öğrenilen ders: {item.Lesson.Lesson}\n  Yöntem: {item.Lesson.LearningMethod}\n  Kaynaklar: {string.Join(", ", item.Lesson.Sources)}"));
    }

    public async Task LearnAsync(
        string question, string answer, string[] sources, CancellationToken cancellationToken, string? learningMethod = null)
    {
        if (sources.Length == 0 || string.IsNullOrWhiteSpace(answer)) return;
        var lessons = await LoadAsync(cancellationToken);
        var now = DateTimeOffset.UtcNow.ToString("O");
        var compact = answer.Length > 1000 ? answer[..1000] : answer;
        lessons.RemoveAll(item => Similar(item.Question, question));
        lessons.Add(new(
            question.Length > 500 ? question[..500] : question,
            compact,
            sources.Take(6).ToArray(),
            string.IsNullOrWhiteSpace(learningMethod)
                ? "İhtiyacı belirle → webde ara → ilgili bölümleri çıkar → kaynaklı cevap üret → sonucu değerlendir"
                : learningMethod,
            now, now, 1));
        var cutoff = DateTimeOffset.UtcNow.AddDays(-180);
        lessons = lessons.Where(item => item.UseCount > 1 || !DateTimeOffset.TryParse(item.LastUsedAt, out var used) || used >= cutoff)
            .OrderByDescending(item => item.UseCount).ThenByDescending(item => item.LastUsedAt).Take(300).ToList();
        await SaveAsync(lessons, cancellationToken);
    }

    public async Task PruneAsync(CancellationToken cancellationToken)
    {
        var lessons = await LoadAsync(cancellationToken);
        var cutoff = DateTimeOffset.UtcNow.AddDays(-180);
        var kept = lessons.Where(item => item.UseCount > 1 || !DateTimeOffset.TryParse(item.LastUsedAt, out var used) || used >= cutoff)
            .OrderByDescending(item => item.UseCount).ThenByDescending(item => item.LastUsedAt).Take(300).ToList();
        if (kept.Count != lessons.Count) await SaveAsync(kept, cancellationToken);
    }

    private static bool Similar(string first, string second)
    {
        var a = Tokenize(first);
        var b = Tokenize(second);
        return a.Count > 0 && a.Intersect(b, StringComparer.OrdinalIgnoreCase).Count() >= Math.Min(3, a.Count);
    }
    private static List<string> Tokenize(string text) => Words.Matches(text.ToLowerInvariant()).Select(match => match.Value).Distinct().ToList();
    private static async Task<List<LearnedLesson>> LoadAsync(CancellationToken cancellationToken)
    {
        try
        {
            return JsonSerializer.Deserialize<List<LearnedLesson>>(await File.ReadAllTextAsync(FilePath, cancellationToken), AppSettings.JsonOptions) ?? [];
        }
        catch { return []; }
    }
    private static async Task SaveAsync(List<LearnedLesson> lessons, CancellationToken cancellationToken)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(FilePath)!);
        await File.WriteAllTextAsync(FilePath, JsonSerializer.Serialize(lessons, AppSettings.JsonOptions), cancellationToken);
    }
}
