namespace LocalAIOS;

internal static class ConversationShortcut
{
    public static bool TryAnswer(string request, out string answer)
    {
        var text = request.Trim().Trim('.', '!', '?').ToLowerInvariant();
        answer = text switch
        {
            "selam" or "merhaba" or "hey" => "Selam! Nasıl yardımcı olabilirim?",
            "teşekkürler" or "teşekkür ederim" or "sağ ol" or "sağol" => "Rica ederim. Başka ne yapmamı istersin?",
            _ => ""
        };
        return answer.Length > 0;
    }
}
