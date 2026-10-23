import fs from "node:fs/promises";
import path from "node:path";

export class MemoryStore {
  constructor(workspace, config) {
    this.enabled = config.enabled;
    this.file = path.resolve(workspace, config.file);
    this.limit = config.maxEntriesForContext;
  }

  async recent() {
    if (!this.enabled) return [];
    try {
      const lines = (await fs.readFile(this.file, "utf8")).trim().split(/\r?\n/).filter(Boolean);
      return lines.slice(-this.limit).map((line) => JSON.parse(line));
    } catch (error) {
      if (error.code === "ENOENT") return [];
      throw error;
    }
  }

  async remember(entry) {
    if (!this.enabled) return;
    await fs.mkdir(path.dirname(this.file), { recursive: true });
    await fs.appendFile(this.file, `${JSON.stringify(entry)}\n`, "utf8");
  }
}
