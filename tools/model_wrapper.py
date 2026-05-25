#!/usr/bin/env python3
"""
model_wrapper.py — Minimal unified interface for local (Ollama) and remote (OpenRouter) models.
Usage:
    python model_wrapper.py --model llama3.1:8b --prompt-file prompts/test.txt
    python model_wrapper.py --model openai/gpt-4.1 --prompt-file prompts/test.txt --api-key sk-xxx
"""
import os, sys, argparse, json, subprocess, textwrap, time


def run_ollama(model, prompt, url="http://localhost:11434"):
    import requests
    resp = requests.post(f"{url}/api/generate", json={"model": model, "prompt": prompt, "stream": False}, timeout=300)
    resp.raise_for_status()
    return resp.json()["response"]


def run_openrouter(model, prompt, api_key=None):
    key = api_key or os.environ.get("OPENROUTER_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("No API key. Set OPENROUTER_KEY or pass --api-key.")
    import requests
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def main():
    p = argparse.ArgumentParser(description="Run a prompt through a model")
    p.add_argument("--model", required=True, help="Model ID, e.g. llama3.1:8b or openai/gpt-4.1")
    p.add_argument("--prompt-file", required=True, help="Path to text file containing the prompt")
    p.add_argument("--api-key", default=None, help="API key (or use env var)")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    args = p.parse_args()

    with open(args.prompt_file) as f:
        prompt = f.read()

    if "/" in args.model or args.model.startswith("gpt-") or args.api_key:
        provider = "openrouter"
        response = run_openrouter(args.model, prompt, args.api_key)
    else:
        provider = "ollama"
        response = run_ollama(args.model, prompt)

    if args.json:
        print(json.dumps({"model": args.model, "provider": provider, "prompt": prompt, "response": response}, indent=2))
    else:
        print(response)


if __name__ == "__main__":
    main()
