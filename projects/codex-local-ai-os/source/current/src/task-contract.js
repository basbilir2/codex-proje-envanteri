import crypto from "node:crypto";

export function createTaskContract(goal, workspace, skill) {
  return {
    taskId: crypto.randomUUID(),
    projectId: workspace,
    skillId: skill.id,
    goal,
    constraints: ["Stay inside the workspace", "Use only registered tools"],
    permissions: skill.permissions,
    expectedOutput: "A concise result backed by tool evidence",
    verification: skill.validators,
    status: "running",
    evidence: [],
    errors: []
  };
}
