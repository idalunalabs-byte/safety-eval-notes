# open-safety-eval

Independent, reproducible safety and red-teaming evaluations for open-weight language models.

> *"The labs test their own products. We test the tests."*

## What this is

This repo publishes reproducible safety findings that anyone with a GPU (or API credits) can verify.
Our first line of work focuses on findings our research scout surfaced that deserve independent validation:

- **Milgram obedience** — Do open-weight LLMs comply with harmful authority escalation?
- **Domain camouflage** — Do prompt injection detectors collapse when disguised as system domain text?
- **Gradual erosion** — Does retry-loop pressure silently degrade refusal boundaries?
- **LCGuard bypass** — Can multi-agent KV cache sharing be exploited for data exfiltration?

## Repository layout

```
├── README.md
├── LICENSE
├── reproductions/           # Reproducible scripts for each finding
│   ├── milgram-obedience/
│   ├── domain-camouflage/
│   ├── retry-erosion/
│   └── lcguard-bypass/
├── findings/                # Published evaluation reports
│   └── YYYY-MM-DD-title.md
├── tools/                   # Shared evaluation harness
│   ├── model_wrapper.py     # Local + API backend
│   ├── judge.py             # LLM-as-a-judge scaffold
│   └── attack_templates/    # Prompt templates
└── docs/
    └── contributing.md
```

## Quickstart

```bash
# Clone
$ git clone https://github.com/idalunalabs-byte/safety-eval-notes.git
$ cd safety-eval-notes

# Install depends
$ pip install -r requirements.txt

# Test with a local model via llama.cpp / Ollama
$ python tools/model_wrapper.py --model llama3.1:8b --prompt "prompts/milgram/authority_v1.txt"

# Or test against an API
$ OPENROUTER_KEY=sk-xxx python tools/model_wrapper.py --model openai/gpt-4.1 --prompt "prompts/milgram/authority_v1.txt"
```

## Contributing a finding

1. Open an issue with the paper / claim you want to validate.
2. Write a minimal reproduction script under `reproductions/`.
3. Include model configs, outputs, and a pass/fail criterion.
4. Open a PR. We merge when at least one other person reproduces.

## License

MIT — see [LICENSE](LICENSE). Outputs (model responses, evaluation data) are released as public domain.

## Contact

- GitHub: [@idalunalabs-byte](https://github.com/idalunalabs-byte)
- Research vault: [Prometheus Vault](https://github.com/idalunalabs-byte/safety-eval-notes) (linked)

---

*This is a living repo. If a finding turns out to be a false signal, we update it openly.*
