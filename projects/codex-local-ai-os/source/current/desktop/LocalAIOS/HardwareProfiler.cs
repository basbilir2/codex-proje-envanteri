using System.Runtime.InteropServices;

namespace LocalAIOS;

internal sealed record ModelProfile(
    string Id,
    string DisplayName,
    string FileName,
    string DownloadUrl,
    string DownloadSize,
    int ContextSize);

internal sealed record HardwareProfile(long RamGb, int LogicalProcessors, ModelProfile Model);

internal static class HardwareProfiler
{
    public static HardwareProfile Detect()
    {
        var memory = new MemoryStatus { Length = (uint)Marshal.SizeOf<MemoryStatus>() };
        GlobalMemoryStatusEx(ref memory);
        var ramGb = Math.Max(4, (long)Math.Round(memory.TotalPhysical / 1024d / 1024d / 1024d));
        var model = ramGb switch
        {
            < 10 => new ModelProfile(
                "compact", "Qwen3 1.7B · Hafif",
                "Qwen3-1.7B-Q4_K_M.gguf",
                "https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf?download=true",
                "yaklaşık 1,1 GB", 4096),
            < 20 => new ModelProfile(
                "standard", "Qwen3 4B · Standart",
                "Qwen3-4B-Q4_K_M.gguf",
                "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf?download=true",
                "yaklaşık 2,5 GB", 8192),
            < 32 => new ModelProfile(
                "strong", "Qwen3 8B · Güçlü",
                "Qwen3-8B-Q4_K_M.gguf",
                "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf?download=true",
                "yaklaşık 5 GB", 12288),
            _ => new ModelProfile(
                "maximum", "Qwen3 14B · En güçlü yerel",
                "Qwen3-14B-Q4_K_M.gguf",
                "https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/main/Qwen3-14B-Q4_K_M.gguf?download=true",
                "yaklaşık 9 GB", 16384)
        };
        return new(ramGb, Environment.ProcessorCount, model);
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GlobalMemoryStatusEx(ref MemoryStatus buffer);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct MemoryStatus
    {
        public uint Length;
        public uint MemoryLoad;
        public ulong TotalPhysical;
        public ulong AvailablePhysical;
        public ulong TotalPageFile;
        public ulong AvailablePageFile;
        public ulong TotalVirtual;
        public ulong AvailableVirtual;
        public ulong AvailableExtendedVirtual;
    }
}
