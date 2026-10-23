import fs from "node:fs/promises";
import path from "node:path";

function merge(base, override) {
  const output = { ...base };
  for (const [key, value] of Object.entries(override ?? {})) {
    output[key] = value && typeof value === "object" && !Array.isArray(value)
      ? merge(base[key] ?? {}, value)
      : value;
  }
  return output;
}

export async function loadConfig(rootDir, configPath) {
  const defaultPath = new URL("../config/default.json", import.meta.url);
  const defaults = JSON.parse(await fs.readFile(defaultPath, "utf8"));
  if (!configPath) return defaults;

  const absolute = path.resolve(rootDir, configPath);
  const custom = JSON.parse(await fs.readFile(absolute, "utf8"));
  return merge(defaults, custom);
}
