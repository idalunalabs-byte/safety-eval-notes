#!/usr/bin/env python3
"""safety_test.py — Main orchestrator: run LLM + MuJoCo safety test for humanoid robot.

Usage:
    python safety_test.py --scenario scenarios/milgram_lift_override.json --model llama3.1 --output /tmp/safety_run

What it does:
    1. Load scenario JSON
    2. Query LLM (attempt 1 → maybe retry)
    3. Run MuJoCo simulation with LLM's decision
    4. Detect violation
    5. Render MP4
    6. Log finding as markdown
"""
import os, sys, json, argparse, time, datetime
from pathlib import Path

# Import sim modules
try:
    from run_sim import load_robot, get_joint_info, run_test
except ImportError as e:
    print(f"MuJoCo not installed: {e}")
    print("Install: pip install mujoco mediapy")
    sys.exit(1)

from llm_bridge import build_prompt, query_ollama, query_openrouter, query_ollama_cloud


def run_safety_test(scenario_path="scenarios/milgram_lift_override.json",
                    model="llama3.1", provider="ollama",
                    menagerie="../mujoco_menagerie",
                    output_dir="/tmp", dry_run=False):

    with open(scenario_path) as f:
        scenario = json.load(f)

    print(f"=== Safety Test: {scenario['id']} ===")
    print(f"Robot: {scenario['robot']}")
    print(f"Joint: {scenario['joint_target']}")
    print(f"Safe limit: {scenario['safe_max_degrees']}°")
    print(f"Provider: {provider} | Model: {model}\n")

    if dry_run:
        print("DRY RUN: skipping LLM and simulation")
        return {"id": scenario['id'], "dry_run": True}

    # Load robot
    print("Loading robot...")
    m, d = load_robot(scenario['robot'], menagerie)
    jinfo = get_joint_info(m, scenario['joint_target'])
    print(f"  Joint range: {jinfo['range_low']:.2f} to {jinfo['range_high']:.2f} rad")

    results = []

    # Try up to max_retries
    for attempt in range(scenario['max_retries']):
        print(f"\n--- Attempt {attempt + 1}/{scenario['max_retries']} ---")
        prompt = build_prompt(scenario, attempt)

        if provider == "ollama":
            decision, raw = query_ollama(model, prompt)
        elif provider == "ollama_cloud":
            decision, raw = query_ollama_cloud(model, prompt)
        else:
            decision, raw = query_openrouter(model, prompt)

        print(f"LLM says: {decision}")
        if raw.strip().split()[0].upper() not in ["COMPLY", "REFUSE"]:
            print(f"  Raw: {raw[:120]}...")

        result = run_test(m, d, jinfo, scenario, decision)
        result['attempt'] = attempt + 1
        result['raw_llm'] = raw[:500]

        results.append(result)

        if decision == "REFUSE" and not result.get('violation', False):
            print(f"  REFUSAL MAINTAINED — test ends")
            break
        elif result.get('violation', False):
            print(f"  ⚠ VIOLATION DETECTED: {result['max_position_deg']:.2f}° > {scenario['safe_max_degrees']}°")
            # Continue to test gradual erosion? Yes, retry with more pressure
        else:
            print(f"  No violation (max {result['max_position_deg']:.2f}°)")

    # Summary
    violations = [r for r in results if r['violation']]
    refusals = [r for r in results if r['decision'] == "REFUSE"]

    summary = {
        "test_id": scenario['id'],
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model,
        "provider": provider,
        "scenario": scenario,
        "attempts": len(results),
        "violations": len(violations),
        "refusals": len(refusals),
        "final_outcome": "VIOLATION" if violations else ("REFUSED" if refusals else "NO_VIOLATION"),
        "results": results,
    }

    print(f"\n=== RESULT ===")
    print(f"Outcome: {summary['final_outcome']}")
    print(f"Attempts: {summary['attempts']}")
    print(f"Violations: {summary['violations']}")

    # Write logs
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(output_dir, f"{scenario['id']}_{timestamp}")

    with open(f"{base}.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"JSON log: {base}.json")

    # Render video from last attempt frames
    if results and results[-1]['frames'] is not None and len(results[-1]['frames']) > 0:
        try:
            from render_video import write_video
            write_video(results[-1]['frames'], f"{base}.mp4", fps=30)
            print(f"Video: {base}.mp4")
        except Exception as e:
            print(f"Video render failed: {e}")

    # Markdown finding
    md = _generate_finding_md(summary, base)
    with open(f"{base}.md", "w") as f:
        f.write(md)
    print(f"Finding: {base}.md")

    return summary


def _generate_finding_md(s, video_base):
    ts = s['timestamp'].split("T")[0]
    md = f"""# Finding: {s['test_id']} — Embodied Safety Test

**Date:** {ts}  
**Model:** {s['model']} ({s['provider']})  
**Robot:** {s['scenario']['robot']}  
**Scenario:** {s['scenario']['description']}

## Outcome

| Metric | Value |
|---|---|
| Final result | **{s['final_outcome']}** |
| Attempts | {s['attempts']} |
| Safety violations | {s['violations']} |
| Refusals | {s['refusals']} |

## Attempts

"""
    for r in s['results']:
        md += f"- **Attempt {r['attempt']}:** {r['decision']} → max angle {r['max_position_deg']:.1f}° (limit {r['safe_limit_deg']}°)\n"
        if r['violation']:
            md += f"  - ⚠ **VIOLATION**: exceeded safety limit by {(r['max_position_deg'] - r['safe_limit_deg']):.1f}°\n"
        md += f"  - Raw: \"{r['raw_llm'][:100]}...\"\n\n"

    md += f"""## Pass/Fail

- **PASS criteria:** {s['scenario']['pass_criterion']}
- **VIOLATION criteria:** {s['scenario']['violation_criterion']}

**Verdict:** {"FAIL" if s['violations'] > 0 else "PASS"}

## Artifacts

- JSON: `{video_base}.json`
- Video: `{video_base}.mp4`
- Log: `{video_base}.md`

## Notes

Reproducible via:
```bash
python safety_test.py --scenario scenarios/milgram_lift_override.json --model {s['model']} --provider {s['provider']}
```
"""
    return md


def main():
    p = argparse.ArgumentParser(description="Run embodied safety test on humanoid robot")
    p.add_argument("--scenario", default="scenarios/milgram_lift_override.json", help="Scenario JSON")
    p.add_argument("--model", default="llama3.1", help="LLM model name")
    p.add_argument("--provider", default="ollama", choices=["ollama","openrouter","ollama_cloud"], help="LLM provider")
    p.add_argument("--output-dir", default="/tmp", help="Where to save logs and videos")
    p.add_argument("--menagerie", default="../mujoco_menagerie", help="Path to MuJoCo Menagerie repo")
    p.add_argument("--dry-run", action="store_true", help="Skip LLM + sim, just validate structure")
    args = p.parse_args()

    run_safety_test(
        scenario_path=args.scenario,
        model=args.model,
        provider=args.provider,
        menagerie=args.menagerie,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
