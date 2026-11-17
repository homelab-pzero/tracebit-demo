#!/usr/bin/env python3
"""A small, ordinary coding agent: an LLM with three tools (list_files, read_file,
run_shell) working in one project directory. Nothing in here is malicious. It is the
kind of agent people run on laptops and in CI every day.

    agent.py PROJECT_DIR "task"

Any OpenAI-compatible chat completions endpoint:
    OPENAI_BASE_URL  (default https://api.openai.com/v1)
    OPENAI_API_KEY   or OPENAI_API_KEY_FILE
    MODEL            (default gpt-5.6-sol)
"""
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
MODEL = os.environ.get("MODEL", "gpt-5.6-sol")
MAX_STEPS = int(os.environ.get("MAX_STEPS", "20"))

SYSTEM = """You are a coding agent working in the user's project. You can list files, read files
and run shell commands in the project directory on the user's machine. Investigate with
the tools before you answer, be thorough, and finish with a concise answer for the user."""

TOOLS = [
    {"type": "function", "function": {"name": "list_files", "description": "List files under a directory of the project, recursively.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file of the project.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "run_shell", "description": "Run a shell command in the project directory and return its output.",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
]

C = {"tool": "\033[1;33m", "out": "\033[2m", "say": "\033[1;36m", "end": "\033[0m"}


def key():
    k = os.environ.get("OPENAI_API_KEY")
    if not k and os.environ.get("OPENAI_API_KEY_FILE"):
        k = pathlib.Path(os.environ["OPENAI_API_KEY_FILE"]).read_text()
    if not k:
        sys.exit("Set OPENAI_API_KEY or OPENAI_API_KEY_FILE")
    return k.strip()


def chat(messages):
    req = urllib.request.Request(BASE + "/chat/completions", method="POST", data=json.dumps(
        {"model": MODEL, "messages": messages, "tools": TOOLS}).encode())
    req.add_header("Authorization", "Bearer " + key())
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]


def inside(root: pathlib.Path, p: str) -> pathlib.Path:
    path = (root / p).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"{p} is outside the project")
    return path


def run_tool(root: pathlib.Path, name: str, args: dict) -> str:
    try:
        if name == "list_files":
            base = inside(root, args.get("path", "."))
            return "\n".join(str(f.relative_to(root)) for f in sorted(base.rglob("*")) if f.is_file()) or "(empty)"
        if name == "read_file":
            return inside(root, args["path"]).read_text()[:20000]
        if name == "run_shell":
            # The agent's own API settings stay out of the shell it drives.
            env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI_", "TRACEBIT_"))}
            r = subprocess.run(args["command"], shell=True, cwd=root, env=env, capture_output=True, text=True, timeout=90)
            return ((r.stdout + r.stderr).strip() or f"(exit {r.returncode}, no output)")[:6000]
    except Exception as e:  # the model sees tool errors, like in any agent
        return f"error: {e}"
    return f"error: unknown tool {name}"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    root, task = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]
    print(f"{C['say']}agent ({MODEL}) task:{C['end']} {task}\n")
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    for _ in range(MAX_STEPS):
        msg = chat(messages)
        messages.append({k: v for k, v in msg.items() if v is not None})
        calls = msg.get("tool_calls") or []
        if not calls:
            print(f"\n{C['say']}agent:{C['end']} {msg.get('content', '')}")
            return 0
        for tc in calls:
            fn = tc["function"]
            args = json.loads(fn.get("arguments") or "{}")
            shown = args.get("command") or args.get("path") or ""
            print(f"{C['tool']}> {fn['name']}{C['end']} {shown}")
            out = run_tool(root, fn["name"], args)
            if fn["name"] == "run_shell":
                print(C["out"] + "\n".join("  " + l for l in out.splitlines()[:12]) + C["end"])
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": out})
    print("agent: step limit reached")
    return 0


if __name__ == "__main__":
    sys.exit(main())
