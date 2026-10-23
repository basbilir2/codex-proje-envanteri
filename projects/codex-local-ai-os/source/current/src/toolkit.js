import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const IGNORED_DIRS = new Set([".git", ".local-ai-os", "node_modules", "dist", "build"]);

function assertInside(workspace, requested = ".") {
  const root = path.resolve(workspace);
  const target = path.resolve(root, requested);
  const relative = path.relative(root, target);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Path is outside the workspace.");
  }
  return target;
}

async function collectFiles(directory, workspace, output, limit) {
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    if (output.length >= limit) return;
    if (entry.isDirectory() && IGNORED_DIRS.has(entry.name)) continue;
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) await collectFiles(full, workspace, output, limit);
    else output.push(path.relative(workspace, full).replaceAll("\\", "/"));
  }
}

function executeProgram(command, args, cwd, timeoutMs) {
  return new Promise((resolve) => {
    let executable = command;
    let programArgs = args;
    if (process.platform === "win32" && command === "npm") {
      const npmCli = (process.env.PATH ?? "")
        .split(path.delimiter)
        .map((directory) => path.join(directory, "node_modules", "npm", "bin", "npm-cli.js"))
        .find(existsSync);
      if (!npmCli) {
        resolve({ ok: false, exitCode: null, stdout: "", stderr: "npm executable could not be resolved." });
        return;
      }
      executable = process.execPath;
      programArgs = [npmCli, ...args];
    }
    const child = spawn(executable, programArgs, { cwd, shell: false, windowsHide: true });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => child.kill(), timeoutMs);
    child.stdout.on("data", (data) => { stdout += data; });
    child.stderr.on("data", (data) => { stderr += data; });
    child.on("error", (error) => {
      clearTimeout(timer);
      resolve({ ok: false, exitCode: null, stdout, stderr: `${stderr}${error.message}` });
    });
    child.on("close", (exitCode) => {
      clearTimeout(timer);
      resolve({ ok: exitCode === 0, exitCode, stdout, stderr });
    });
  });
}

export class Toolkit {
  constructor(workspace, runtime) {
    this.workspace = path.resolve(workspace);
    this.timeoutMs = runtime.commandTimeoutMs;
    this.maxOutput = runtime.maxToolOutputChars;
    this.allowedCommands = new Set(runtime.allowedCommands);
    this.changedFiles = new Set();
  }

  definitions() {
    return [
      {
        type: "function",
        function: {
          name: "list_files",
          description: "List files recursively inside the workspace.",
          parameters: { type: "object", properties: { path: { type: "string" } } }
        }
      },
      {
        type: "function",
        function: {
          name: "read_file",
          description: "Read a UTF-8 text file inside the workspace.",
          parameters: {
            type: "object",
            properties: { path: { type: "string" } },
            required: ["path"]
          }
        }
      },
      {
        type: "function",
        function: {
          name: "write_file",
          description: "Create or replace a UTF-8 text file inside the workspace.",
          parameters: {
            type: "object",
            properties: { path: { type: "string" }, content: { type: "string" } },
            required: ["path", "content"]
          }
        }
      },
      {
        type: "function",
        function: {
          name: "replace_text",
          description: "Replace one exact, unique text block in a workspace file.",
          parameters: {
            type: "object",
            properties: {
              path: { type: "string" },
              oldText: { type: "string" },
              newText: { type: "string" }
            },
            required: ["path", "oldText", "newText"]
          }
        }
      },
      {
        type: "function",
        function: {
          name: "run_command",
          description: "Run an allowed local command in the workspace. Pass arguments separately.",
          parameters: {
            type: "object",
            properties: {
              command: { type: "string" },
              args: { type: "array", items: { type: "string" } }
            },
            required: ["command", "args"]
          }
        }
      }
    ];
  }

  async execute(name, args) {
    try {
      switch (name) {
        case "list_files": {
          const directory = assertInside(this.workspace, args.path ?? ".");
          const files = [];
          await collectFiles(directory, this.workspace, files, 500);
          return { ok: true, files };
        }
        case "read_file": {
          const file = assertInside(this.workspace, args.path);
          const content = await fs.readFile(file, "utf8");
          return { ok: true, content: content.slice(0, this.maxOutput), truncated: content.length > this.maxOutput };
        }
        case "write_file": {
          const file = assertInside(this.workspace, args.path);
          await fs.mkdir(path.dirname(file), { recursive: true });
          await fs.writeFile(file, args.content, "utf8");
          this.changedFiles.add(file);
          return { ok: true, path: path.relative(this.workspace, file) };
        }
        case "replace_text": {
          const file = assertInside(this.workspace, args.path);
          const content = await fs.readFile(file, "utf8");
          const first = content.indexOf(args.oldText);
          if (first < 0) throw new Error("The requested text was not found.");
          if (content.indexOf(args.oldText, first + args.oldText.length) >= 0) {
            throw new Error("The requested text is not unique.");
          }
          await fs.writeFile(file, content.replace(args.oldText, args.newText), "utf8");
          this.changedFiles.add(file);
          return { ok: true, path: path.relative(this.workspace, file) };
        }
        case "run_command": {
          if (!this.allowedCommands.has(args.command)) throw new Error("Command is not allowed by configuration.");
          const result = await executeProgram(args.command, args.args ?? [], this.workspace, this.timeoutMs);
          return {
            ...result,
            stdout: result.stdout.slice(-this.maxOutput),
            stderr: result.stderr.slice(-this.maxOutput)
          };
        }
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }
}

export async function verifyChangedFiles(files) {
  const results = [];
  for (const file of files) {
    const extension = path.extname(file).toLowerCase();
    if (extension === ".json") {
      try {
        JSON.parse(await fs.readFile(file, "utf8"));
        results.push({ file, ok: true, check: "json" });
      } catch (error) {
        results.push({ file, ok: false, check: "json", error: error.message });
      }
    }
    if ([".js", ".mjs", ".cjs"].includes(extension)) {
      const result = await executeProgram(process.execPath, ["--check", file], path.dirname(file), 30000);
      results.push({ file, ok: result.ok, check: "syntax", error: result.stderr.trim() || undefined });
    }
  }
  return results;
}
