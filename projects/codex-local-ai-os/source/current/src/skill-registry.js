import fs from "node:fs/promises";
import path from "node:path";

export class SkillRegistry {
  constructor(skillRoot) {
    this.skillRoot = skillRoot;
    this.skills = [];
  }

  async load() {
    const entries = await fs.readdir(this.skillRoot, { withFileTypes: true });
    this.skills = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const base = path.join(this.skillRoot, entry.name);
      try {
        const manifest = JSON.parse(await fs.readFile(path.join(base, "manifest.json"), "utf8"));
        const instructions = await fs.readFile(path.join(base, "instructions.md"), "utf8");
        this.skills.push({ ...manifest, instructions, base });
      } catch (error) {
        throw new Error(`Skill could not be loaded (${entry.name}): ${error.message}`);
      }
    }
    if (this.skills.length === 0) throw new Error("No skills are installed.");
    return this;
  }

  route(goal) {
    const text = goal.toLocaleLowerCase("tr");
    let best = this.skills[0];
    let bestScore = -1;
    for (const skill of this.skills) {
      const score = (skill.routingKeywords ?? []).reduce(
        (total, keyword) => total + (text.includes(keyword.toLocaleLowerCase("tr")) ? 1 : 0),
        0
      );
      if (score > bestScore) {
        best = skill;
        bestScore = score;
      }
    }
    return best;
  }
}
