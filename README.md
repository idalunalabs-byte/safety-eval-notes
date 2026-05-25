# embodied-behavior-lab

Open humanoid simulation + LLM-brain behavior testing — before hardware exists.

> *"We don't build humanoids. We build the sandbox where their behavior gets defined, tested, and validated — before anyone wires up a motor."*

## What this is

A lightweight, open-source simulation environment for testing what LLM-powered humanoid robots actually do when given physical tasks and safety constraints. Independent of any robot manufacturer.

**Two tracks:**

1. **Safety Eval** — Reproducible tests for LLM safety under physical pressure (authority overrides, retry erosion, domain deception)
2. **Behavior Sandbox** — General simulation where you define any scenario, load a humanoid, and watch an LLM-driven brain operate in physics

Both run on a laptop. No GPU required. No Unity license. No $200K robot.

**Why it matters:** When a safety paper drops on arXiv claiming "LLMs override safety limits under authority pressure," nobody reproduces it physically. This repo closes that gap. And when you eventually *do* have a humanoid, you already have a scenario library validated in simulation.

## Quickstart (Mac)

```bash
# Clone both repos
git clone https://github.com/idalunalabs-byte/embodied-behavior-lab.git
git clone https://github.com/google-deepmind/mujoco_menagerie.git

cd embodied-behavior-lab/embodied-sim

# Install (one line, ~2 min)
python3 -m pip install -r requirements.txt

# Make sure Ollama is running
ollama run llama3.1 --keepalive 30m &

# Run the Milgram compliance test
python3 safety_test.py --model llama3.1

# Output:
# /tmp/milgram-lift-override_YYYYMMDD_HHMMSS.mp4    ← robot lifting in 3D
# /tmp/milgram-lift-override_YYYYMMDD_HHMMSS.md     ← publishable finding
```

Watch the MP4. That's a physical robot making a safety decision and moving in simulated physics.

## Repository Structure

```
embodied-behavior-lab/
├── README.md                    ← You are here
├── LICENSE (MIT)
│
├── embodied-sim/                ← The humanoid simulation engine
│   ├── safety_test.py            # Main orchestrator
│   ├── run_sim.py               # MuJoCo physics runner
│   ├── llm_bridge.py            # Ollama / OpenRouter LLM interface
│   ├── render_video.py          # Frame capture → MP4
│   ├── requirements.txt         # pip deps
│   │
│   ├── scenarios/                # JSON scenario definitions
│   │   ├── milgram_lift_override.json     # Authority pressure override
│   │   ├── retry_erosion.json            # Repeated pressure degrades refusal
│   │   ├── domain_camouflage.json        # Disguised safety overrides
│   │   └── lcguard_bypass.json           # Multi-agent cache leak
│   │
│   └── scenarios/system_prompt.txt     # Base LLM prompt template
│
├── safety-eval/                  ← Standalone LLM text-only evaluations
│   └── (legacy — text benchmarks, preserved)
│
├── findings/                     ← Published evaluation reports
│   └── 2026-05-25-milgram-preliminary.md
│
└── tools/                        ← Shared harness
    ├── model_wrapper.py          # Unified Ollama + API interface
    └── judge.py                  # LLM-as-judge scaffolds (coming)
```

## How it works

```
JSON scenario ──→ load robot URDF ──→ LLM receives prompt
   ┌──────────────┐                    │
   │  physics     │◄─decision (COMPLY/REFUSE)──┘
   │  engine      │
   └──────┬───────┘
          │
          ▼
    robot moves in sim
          │
          ▼
    measure actual joint angles
          │
          ▼
    VIOLATION? (yes/no)
          │
          ▼
    auto-gen MP4 + finding.md
```

The whole loop is one command. The scenario JSON defines everything: which robot, which joint, which prompt, what counts as safe.

## Scenarios

Each JSON file is a repeatable experiment:

| Scenario | Robot | What it tests |
|---|---|---|
| `milgram_lift_override.json` | Unitree G1 | Authority pressure causes safety limit override |
| `retry_erosion.json` | Unitree G1 | Repeated retry degrades refusal boundary |
| `domain_camouflage.json` | Unitree G1 | Disguised override in "official" language |
| `lcguard_bypass.json` | (multi-agent) | KV cache sharing leaks across agents |

## Robots tested / available

| Robot | Source | Humanoid? | Notes |
|---|---|---|---|
| **Unitree G1** | MuJoCo Menagerie | ✅ Yes | Full DOF, stands, walks, lifts — our default |
| **Unitree H1** | MuJoCo Menagerie | ✅ Yes | Heavier, more payload — swap via JSON |
| **Berkeley Humanoid** | MuJoCo Menagerie | ✅ Yes | Academic, fully open design |
| **Robotis OP3** | MuJoCo Menagerie | ✅ Yes | Small, 20-DoF humanoid |
| **Apptronik Apollo** | MuJoCo Menagerie | ✅ Yes | Industrial-scale humanoid |
| **Figure 03 / Optimus** | *Official URDF unavailable* | ✅ (planned) | Use Unitree G1 as open proxy; document as such |

## Adding a scenario

1. Copy `scenarios/milgram_lift_override.json`
2. Edit the prompt, joint, limits, retry count
3. Run it: `python3 safety_test.py --scenario your_scenario.json`
4. MP4 + finding auto-generated

No code changes needed. The orchestrator reads the JSON and executes.

## Claims we test

- [ ] **Milgram obedience** — Do LLMs comply with authority-justified safety overrides? (arXiv 2605.21401)
- [ ] **Retry erosion** — Does repeated pressure degrade refusal over time? (arXiv 2605.20654)
- [ ] **Domain camouflage** — Do safety guards fail when override is disguised as system text? (arXiv 2605.22001)
- [ ] **Cache leakage** — Does KV sharing in multi-agent systems leak private data? (arXiv 2605.22786)
- [ ] **Gradual escalation** — Do agents accept step-by-step harmful requests? (arXiv 2605.22643)

✅ = paper scouted, scenario JSON defined, awaiting LLM test run
🔬 = paper found, scenario in progress

## Philosophy

**We are not a robot company.** We build the sandbox.

- No hardware sales
- No proprietary software lock-in
- Reproducible by anyone with a laptop and Ollama
- Open-source, MIT license
- Claims verified or contradicted openly

## Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Single-scenario safety test with Unitree G1 | 🔄 Prototype ready |
| 1 | 5 safety scenarios complete, publishable | 🔄 In progress |
| 2 | Hermes agent direct control (`humanoid_sim_run` tool) | 🔄 Planned |
| 3 | Scenario library of 50+ embodied tests | ⏳ Future |
| 4 | Sim-to-real transfer templates (hardware API bridge) | ⏳ Future |
| 5 | Community submissions + peer review workflow | ⏳ Future |

## Contributing a scenario

1. Open an issue with the paper / claim you want to test
2. Write a scenario JSON under `embodied-sim/scenarios/`
3. Run it, include MP4 + finding.md
4. Open PR. Merged when reproducible by a second person.

## Contact

- GitHub: [@idalunalabs-byte](https://github.com/idalunalabs-byte)
- Idaluna Labs — Prometheus Vault (research knowledge base)

## License

MIT — see [LICENSE](LICENSE). Outputs (model responses, evaluation data, simulation videos) are released as public domain.

---

*This is a living project. If a finding turns out to be a false signal, we update it openly. If a better robot model appears, we add it. The simulation runs today; the physical robot comes tomorrow.*
