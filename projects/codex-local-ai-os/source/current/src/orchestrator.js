import path from "node:path";
import { fileURLToPath } from "node:url";
import { SkillRegistry } from "./skill-registry.js";
import { createTaskContract } from "./task-contract.js";
import { OllamaClient } from "./model-client.js";
import { MemoryStore } from "./memory-store.js";
import { Toolkit, verifyChangedFiles } from "./toolkit.js";

function systemPrompt(skill, contract, memories) {
  const memoryText = memories.length
    ? memories.map((item) => `- ${item.goal}: ${item.outcome}`).join("\n")
    : "No relevant prior task memory.";
  return `You are the Executive Brain of a local-first AI system.
You are using the ${skill.name} skill. Follow its instructions exactly.

${skill.instructions}

Task contract:
${JSON.stringify(contract, null, 2)}

Recent project experience:
${memoryText}

Operating rules:
- Inspect before editing.
- Stay inside the workspace and keep changes narrowly scoped.
- Use tools for claims about files, commands, builds, or tests.
- Do not repeat a failed action without changing the approach.
- Run only checks proportionate to the change.
- Answer in the user's language and keep the final response concise.`;
}

function normalizeArguments(value) {
  if (value && typeof value === "object") return value;
  if (typeof value === "string") {
    try { return JSON.parse(value); } catch { return {}; }
  }
  return {};
}

export async function runTask({ goal, workspace, config, onStatus = () => {} }) {
  const skillRoot = fileURLToPath(new URL("../skills", import.meta.url));
  const registry = await new SkillRegistry(skillRoot).load();
  const skill = registry.route(goal);
  const contract = createTaskContract(goal, workspace, skill);
  const memory = new MemoryStore(workspace, config.memory);
  const memories = await memory.recent();
  const toolkit = new Toolkit(workspace, config.runtime);
  const model = new OllamaClient(config.coreModel);
  const modelName = await model.initialize();
  onStatus(`Model: ${modelName} | Skill: ${skill.id}`);

  const messages = [
    { role: "system", content: systemPrompt(skill, contract, memories) },
    { role: "user", content: goal }
  ];

  let finalText = "";
  for (let step = 0; step < config.runtime.maxSteps; step += 1) {
    const message = await model.chat(messages, toolkit.definitions());
    messages.push(message);
    const calls = message.tool_calls ?? [];
    if (calls.length === 0) {
      finalText = message.content?.trim() ?? "";
      break;
    }

    for (const call of calls) {
      const name = call.function?.name;
      const args = normalizeArguments(call.function?.arguments);
      const result = await toolkit.execute(name, args);
      contract.evidence.push({ tool: name, ok: result.ok });
      if (!result.ok) contract.errors.push({ tool: name, error: result.error });
      messages.push({ role: "tool", tool_name: name, content: JSON.stringify(result) });
    }
  }

  if (!finalText) finalText = "The task stopped before a final answer was produced.";
  const verification = await verifyChangedFiles(toolkit.changedFiles);
  const failedChecks = verification.filter((item) => !item.ok);
  contract.status = failedChecks.length ? "verification_failed" : "completed";
  contract.evidence.push(...verification);

  await memory.remember({
    timestamp: new Date().toISOString(),
    taskId: contract.taskId,
    skillId: skill.id,
    goal: goal.slice(0, 1000),
    outcome: finalText.slice(0, 1500),
    changedFiles: [...toolkit.changedFiles].map((file) => path.relative(workspace, file)),
    status: contract.status
  });

  if (failedChecks.length) {
    finalText += `\n\nVerification warning: ${failedChecks.map((item) => `${path.basename(item.file)} (${item.check})`).join(", ")}`;
  }
  return { text: finalText, contract };
}
