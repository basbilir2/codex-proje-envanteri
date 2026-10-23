#!/usr/bin/env node
import path from "node:path";
import process from "node:process";
import readline from "node:readline/promises";
import { loadConfig } from "./config.js";
import { runTask } from "./orchestrator.js";

function parseArgs(argv) {
  const options = { workspace: process.cwd(), configPath: null, model: null, memory: true, goal: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--workspace") options.workspace = argv[++index];
    else if (value === "--config") options.configPath = argv[++index];
    else if (value === "--model") options.model = argv[++index];
    else if (value === "--no-memory") options.memory = false;
    else options.goal.push(value);
  }
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const workspace = path.resolve(options.workspace);
  const config = await loadConfig(workspace, options.configPath);
  if (options.model) config.coreModel.model = options.model;
  if (!options.memory) config.memory.enabled = false;

  let goal = options.goal.join(" ").trim();
  if (!goal) {
    const terminal = readline.createInterface({ input: process.stdin, output: process.stdout });
    goal = (await terminal.question("Ne yapmamı istersin? ")).trim();
    terminal.close();
  }
  if (!goal) throw new Error("A task is required.");

  const result = await runTask({ goal, workspace, config });
  process.stdout.write(`${result.text}\n`);
}

main().catch((error) => {
  process.stderr.write(`Hata: ${error.message}\n`);
  process.exitCode = 1;
});
