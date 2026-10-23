"""Check configuration and real OpenCode parallel dispatch; --live also probes NIM.

Offline responses are explicitly simulated. They never prove NVIDIA access.
No third-party Python dependencies and no credential logging.
"""
import argparse
import concurrent.futures
import copy
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent.parent / "work" / "smoke"
MODELS = {
    "deepseek": "deepseek-ai/deepseek-v4.1-flash",
    "glm": "z-ai/glm-5.3",
    "nemotron": "nvidia/nemotron-3.5-super-vl-120b-a12b",
}
BASE = "https://integrate.api.nvidia.com/v1"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def run_cli(cli, args, env, cwd=WORK, timeout=90):
    # Use the executable directly, avoiding the shell and command interpolation.
    p = subprocess.run([str(cli), *args], cwd=cwd, env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"OpenCode command failed ({p.returncode}): "
                           + p.stderr[-1500:])
    return p.stdout


def isolated_env(config):
    env = os.environ.copy()
    env["OPENCODE_CONFIG"] = str(config)
    env.pop("OPENCODE_CONFIG_CONTENT", None)
    env.pop("OPENCODE_CONFIG_DIR", None)
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    for name, folder in [("XDG_CONFIG_HOME", "config"),
                         ("XDG_DATA_HOME", "data"),
                         ("XDG_CACHE_HOME", "cache"),
                         ("XDG_STATE_HOME", "state")]:
        env[name] = str(WORK / folder)
    return env


def check_config(config, cli):
    assert config["enabled_providers"] == ["nvidia-nim"]
    assert config["default_agent"] == "deepseek"
    assert config["share"] == "disabled"
    provider = config["provider"]["nvidia-nim"]
    assert provider["options"]["baseURL"] == BASE
    assert provider["options"]["apiKey"] == "{env:NVIDIA_API_KEY}"
    for agent, model in MODELS.items():
        assert config["agent"][agent]["model"] == "nvidia-nim/" + model
        assert model in provider["models"]
    assert config["agent"]["nemotron"]["permission"]["edit"]["*"] == "deny"
    env = isolated_env(ROOT / "opencode.json")
    # Validate with a non-secret key; debug config would otherwise expose the key.
    env["NVIDIA_API_KEY"] = "offline-config-validation"
    resolved = json.loads(run_cli(cli, ["debug", "config"], env))
    for name in MODELS:
        assert len(resolved["agent"][name]["prompt"]) > 200
    available = run_cli(cli, ["models", "nvidia-nim"], env)
    assert all("nvidia-nim/" + model in available for model in MODELS.values())
    return {"status": "passed", "version": run_cli(cli, ["--version"], env).strip(),
            "models": MODELS, "prompts_resolved": True}


def smoke_config(config, url):
    config = copy.deepcopy(config)
    config["provider"]["nvidia-nim"]["options"]["baseURL"] = url
    config["provider"]["nvidia-nim"]["options"]["apiKey"] = "offline-simulation"
    for name, agent in config["agent"].items():
        agent["prompt"] = (ROOT / "prompts" / (name + ".md")).read_text(encoding="utf-8")
        agent["steps"] = 8
        agent.setdefault("permission", {}).update({"edit": "deny", "bash": "deny",
                                                  "external_directory": "deny"})
    return config


def offline_dispatch(config, cli):
    intervals = []
    tool_schemas = []
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            model = data.get("model", "")
            start = time.monotonic()
            calls = None
            tools = {t["function"]["name"]: t for t in data.get("tools", [])}
            has_result = any(m.get("role") == "tool" for m in data.get("messages", []))
            if model == MODELS["deepseek"] and not has_result and "task" in tools:
                with lock:
                    tool_schemas.append(tools["task"]["function"])
                calls = [{"index": i, "id": f"probe_{name}", "type": "function",
                          "function": {"name": "task", "arguments": json.dumps({
                              "description": f"{name} receipt test",
                              "subagent_type": name,
                              "prompt": f"Read-only smoke test. Reply exactly {name.upper()}_OK. No tools."})}}
                         for i, name in enumerate(("glm", "nemotron"))]
                delta = {"role": "assistant", "tool_calls": calls}
                finish = "tool_calls"
            else:
                if model != MODELS["deepseek"]:
                    time.sleep(0.8)
                name = next((a for a, m in MODELS.items() if m == model), "unknown")
                content = ("DEEPSEEK_OK GLM_OK NEMOTRON_OK" if name == "deepseek"
                           else name.upper() + "_OK")
                delta, finish = {"role": "assistant", "content": content}, "stop"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for d, f in ((delta, None), ({}, finish)):
                chunk = {"id": "chatcmpl-offline", "object": "chat.completion.chunk",
                         "created": int(time.time()), "model": model,
                         "choices": [{"index": 0, "delta": d, "finish_reason": f}]}
                self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            with lock:
                intervals.append({"model": model, "start": start, "end": time.monotonic()})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    path = WORK / "offline-opencode.json"
    path.write_text(json.dumps(smoke_config(config,
                    f"http://127.0.0.1:{server.server_port}/v1")), encoding="utf-8")
    env = isolated_env(path)
    env["NVIDIA_API_KEY"] = "offline-simulation"
    try:
        output = run_cli(cli, ["run", "--format", "json", "--agent", "deepseek",
                              "Read-only smoke test. Delegate receipt probes to glm and nemotron concurrently. "
                              "Use two task tool calls in one response. Collect both results. "
                              "Then answer DEEPSEEK_OK GLM_OK NEMOTRON_OK. No file access or shell."], env)
        (WORK / "offline-events.jsonl").write_text(output, encoding="utf-8")
        children = {a: [r for r in intervals if r["model"] == MODELS[a]]
                    for a in ("glm", "nemotron")}
        assert all(children.values()), "Both child models were not called"
        overlap = any(max(x["start"], y["start"]) < min(x["end"], y["end"])
                      for x in children["glm"] for y in children["nemotron"])
        assert overlap, "Child requests did not overlap"
        assert all(receipt in output for receipt in ("DEEPSEEK_OK", "GLM_OK", "NEMOTRON_OK"))
        return {"status": "passed", "simulated_provider": True,
                "real_opencode_dispatch": True, "child_requests_overlap": overlap,
                "request_count": len(intervals)}
    finally:
        server.shutdown()
        server.server_close()
        if tool_schemas:
            (WORK / "task-schema.json").write_text(json.dumps(tool_schemas[0]), encoding="utf-8")


def live_probe(agent, key):
    start = time.monotonic()
    expected = agent.upper() + "_OK"
    body = {"model": MODELS[agent], "messages": [
        {"role": "user", "content": f"Connectivity test. Reply exactly {expected}; no explanation."}],
        "max_tokens": 512, "stream": True}
    if agent == "deepseek":
        body["reasoning_effort"] = 1
    elif agent == "glm":
        body["reasoning_effort"] = "low"
        body["chat_template_kwargs"] = {"clear_thinking": True}
    req = Request(BASE + "/chat/completions", data=json.dumps(body).encode(),
                  headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        message = ""
        first_byte = None
        with urlopen(req, timeout=60) as response:
            for raw in response:
                if first_byte is None:
                    first_byte = round(time.monotonic() - start, 2)
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                if line[5:].strip() == "[DONE]":
                    break
                data = json.loads(line[5:])
                for choice in data.get("choices", []):
                    message += choice.get("delta", {}).get("content") or ""
                if time.monotonic() - start > 180:
                    raise TimeoutError()
        return {"agent": agent, "model": MODELS[agent],
                "status": "passed" if expected in message else "unexpected_response",
                "seconds": round(time.monotonic() - start, 2),
                "first_byte_seconds": first_byte}
    except HTTPError as e:
        return {"agent": agent, "status": "failed", "http_status": e.code,
                "reason": {401: "invalid_api_key", 402: "insufficient_credits",
                           403: "access_denied", 404: "model_unavailable",
                           429: "rate_limited"}.get(e.code, "provider_error")}
    except (URLError, TimeoutError):
        return {"agent": agent, "status": "failed", "reason": "connection_or_timeout"}


def live_dispatch(config, cli):
    path = WORK / "live-opencode.json"
    scoped = smoke_config(config, BASE)
    scoped["provider"]["nvidia-nim"]["options"]["apiKey"] = "{env:NVIDIA_API_KEY}"
    path.write_text(json.dumps(scoped), encoding="utf-8")
    env = isolated_env(path)
    prompt = (
        "Read-only three-agent connectivity smoke test. Do not inspect files or run commands. "
        "Use the task tool twice in ONE response so both child sessions run concurrently. "
        "Task 1: subagent_type glm; prompt: Reply exactly GLM_OK and use no tools. "
        "Task 2: subagent_type nemotron; prompt: Reply exactly NEMOTRON_OK and use no tools. "
        "Wait for both results, then reply DEEPSEEK_OK GLM_OK NEMOTRON_OK. "
        "This is a small communication test, do not request additional reviews."
    )
    output = run_cli(cli, ["run", "--format", "json", "--agent", "deepseek", prompt],
                     env, timeout=300)
    (WORK / "live-events.jsonl").write_text(output, encoding="utf-8")
    completed = {}
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part", {})
        state = part.get("state", {})
        name = state.get("input", {}).get("subagent_type")
        if part.get("tool") == "task" and name in ("glm", "nemotron"):
            if state.get("status") == "completed":
                completed[name] = state
    assert set(completed) == {"glm", "nemotron"}, "Both real child agents must complete"
    for name, state in completed.items():
        model = state.get("metadata", {}).get("model", {})
        assert model.get("providerID") == "nvidia-nim" and model.get("modelID") == MODELS[name]
        assert name.upper() + "_OK" in state.get("output", "")
    a, b = (completed[n]["time"] for n in ("glm", "nemotron"))
    overlap = max(a["start"], b["start"]) < min(a["end"], b["end"])
    assert overlap, "Real agent tasks did not overlap"
    assert "DEEPSEEK_OK" in output
    return {"status": "passed", "simulated_provider": False,
            "child_tasks_overlap": overlap,
            "children": {n: s["metadata"]["model"] for n, s in completed.items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    cli = args.cli.resolve()
    if cli.suffix == ".cmd":
        cli = cli.parent.parent / "opencode-ai" / "bin" / "opencode.exe"
    WORK.mkdir(parents=True, exist_ok=True)
    config = read_json(ROOT / "opencode.json")
    report = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "production_project_modified": False}
    for name, check in (("configuration", check_config), ("offline_parallel_dispatch", offline_dispatch)):
        try:
            report[name] = check(config, cli)
        except Exception as e:
            report[name] = {"status": "failed", "reason": str(e)[-1800:]}
    report["nvidia_live"] = {"status": "not_run"}
    report["nvidia_live_parallel_agents"] = {"status": "not_run"}
    if args.live:
        key = os.environ.get("NVIDIA_API_KEY", "")
        if not key:
            report["nvidia_live"] = {"status": "blocked", "reason": "NVIDIA_API_KEY_missing"}
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                pending = {pool.submit(live_probe, a, key): a for a in MODELS}
                probes = []
                for done in concurrent.futures.as_completed(pending):
                    probe = done.result()
                    probes.append(probe)
                    print(json.dumps({"live_probe": probe}), flush=True)
            report["nvidia_live"] = {"status": "passed" if all(
                p["status"] == "passed" for p in probes) else "failed", "probes": probes}
            if report["nvidia_live"]["status"] == "passed":
                try:
                    report["nvidia_live_parallel_agents"] = live_dispatch(config, cli)
                except Exception as e:
                    # Do not log raw provider errors: they may contain request details.
                    report["nvidia_live_parallel_agents"] = {
                        "status": "failed", "reason": type(e).__name__}
    destination = ROOT / "reports" / ("live-verification.json" if args.live else "local-verification.json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    checks = [report["configuration"], report["offline_parallel_dispatch"]]
    if args.live:
        checks.append(report["nvidia_live"])
        checks.append(report["nvidia_live_parallel_agents"])
    return 0 if all(c["status"] == "passed" for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
