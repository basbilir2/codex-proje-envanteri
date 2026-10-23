export class OllamaClient {
  constructor(config) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.model = config.model;
    this.temperature = config.temperature;
  }

  async initialize() {
    if (this.model) return this.model;
    let response;
    try {
      response = await fetch(`${this.baseUrl}/api/tags`);
    } catch {
      throw new Error("Ollama is not reachable. Start Ollama and install a local model.");
    }
    if (!response.ok) throw new Error(`Ollama returned HTTP ${response.status}.`);
    const data = await response.json();
    const models = data.models ?? [];
    if (models.length === 0) throw new Error("No local Ollama model is installed.");
    const preferred = models.find((item) => /coder|qwen|llama|mistral|gemma/i.test(item.name));
    this.model = (preferred ?? models[0]).name;
    return this.model;
  }

  async chat(messages, tools) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model: this.model,
        messages,
        tools,
        stream: false,
        options: { temperature: this.temperature }
      })
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`Local model request failed (${response.status}): ${detail.slice(0, 500)}`);
    }
    const data = await response.json();
    if (!data.message) throw new Error("The local model returned an invalid response.");
    return data.message;
  }
}
