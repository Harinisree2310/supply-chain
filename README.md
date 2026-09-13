# 🔗 AutoChain — Autonomous Retail Supply Chain Recovery Agent

**Tech Zephyr 4.0 — Agentic AI Hackathon**
*Problem Statement: Autonomous Retail Supply Chain Recovery Agent*


> An agent that monitors a retail supply chain, detects disruptions the moment they happen, diagnoses root causes, optimizes a recovery plan across cost/time/carbon/reliability, executes it, verifies the outcome, and **replans automatically** if that plan turns out to be wrong — end to end, with zero human decision in the loop.

**🔴 [Live results viewer](https://supply-chain-xofybygvdqgg98qyxhwaco.streamlit.app/)** — see real, recorded agent runs, no install needed
**🎥 [Demo video](#)** — *add your video link here*


---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [What Makes This Genuinely Agentic](#what-makes-this-genuinely-agentic-not-a-scripted-demo)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Sample Run](#sample-run-real-output)
- [Deployment](#deployment)
- [Security](#security)
- [Future Scope](#future-scope)

---

## The Problem

Retail supply chains break constantly, and recovery is still almost entirely manual:

| # | Problem | Why it hurts |
|---|---|---|
| 1 | **Vendors run out of stock** | No automatic fallback to alternative suppliers |
| 2 | **Shipments get delayed** | Disruption often isn't noticed until stock is already critically low |
| 3 | **Recovery decisions are manual** | A human has to compare vendors, costs, and routes under time pressure |
| 4 | **Decisions aren't learned from** | The same underperforming vendor gets re-picked next time |

**Target users:** retail operations and supply chain teams who need continuous, real-time recovery decisions faster than a human can manually reason through them — especially smaller teams without a dedicated 24/7 logistics desk.

**Why this needs an agentic solution, not a dashboard or a static model:** the right recovery action depends on the *current* state of multiple interacting systems (inventory, vendor capacity, shipping routes) that change unpredictably. A fixed rule ("always reorder from vendor B") breaks the moment vendor B is also disrupted. This requires a system that perceives state, retrieves live options, reasons about trade-offs, acts, checks its own result, and adapts — the definition of an agentic loop, not a lookup table.

## The Solution

**AutoChain** is a fully autonomous recovery agent built around one continuous loop:

```
Monitor → Detect → Diagnose → Optimize → Decide → Verify → (replan if blocked)
```

It runs **entirely on your own machine** — no external APIs, no API keys, no internet dependency at runtime. The only AI model involved runs locally via [Ollama](https://ollama.com), and it's used exclusively for *reasoning and justification* — never for retrieving or inventing data.

**Expected impact:** faster recovery from disruptions (autonomous decisions in seconds vs. manual comparison in hours), decisions that improve over time via persistent vendor memory, and full auditability since every decision is deterministic where it needs to be and explained in plain language where it involves judgment.

## What Makes This Genuinely Agentic (Not a Scripted Demo)

- ✅ **Real prioritization** — disruptions are ranked by a computed urgency score, not picked in arbitrary order
- ✅ **Persistent memory across runs** — a vendor blocked in a past run carries a penalty into future decisions, stored in `data/vendor_track_record.json`
- ✅ **Comparative justification** — the agent explains not just why it chose a plan, but why the alternatives lost, citing their real numbers
- ✅ **Live replanning** — a blocked plan automatically excludes that vendor and re-diagnoses, with no human restart
- ✅ **Tested against an unscripted scenario** — verified against a disruption it wasn't specifically hand-tuned for

## Architecture


```
Monitor state → Detect disruption → Diagnose & retrieve options
      ↑                                        ↓
      |                                    Optimize
      |                                        ↓
 (loop back)                          Decide & execute
      ↑                                        ↓
      └──────────── if blocked ──────────  Verify outcome
```

Built as a [LangGraph](https://github.com/langchain-ai/langgraph) state machine. Deterministic tools (data access, cost/carbon math, constraint checks) are kept strictly separate from the single LLM-reasoning step — see [ARCHITECTURE.md](ARCHITECTURE.md) for a full breakdown against every component category (agent/controller, tools, memory, retrieval, planning, verification, failure handling, and why no external systems or RAG layer are used).



## Tech Stack

| Component | Choice | Why |
|---|---|---|
| Agent orchestration | **LangGraph** | Explicit state graph maps directly onto the required demo narrative |
| LLM | **`phi3:mini` via Ollama** | Small, free, fully local — no API key, no cost, no internet dependency |
| Optimization | **Custom weighted scoring** | Deterministic and auditable across cost / time / carbon / reliability |
| Dashboard | **Streamlit** | Live view of agent state, with a button to inject disruptions on demand |
| Data | **Local JSON** | The entire simulated company — hand-editable, fully offline |

## Project Structure

```
supply_chain_agent/
├── data/
│   ├── products.json              # simulated inventory
│   ├── vendors.json                # simulated vendors, deliberately varied trade-offs
│   ├── routes.json                 # simulated shipping routes
│   ├── shipments.json              # simulated in-transit orders
│   ├── constraints.json            # business rules the agent must satisfy
│   ├── vendor_track_record.json    # persistent memory across runs
│   └── demo_logs.json              # auto-generated log of real runs
├── deployed_demo/                  # standalone, deployable results viewer (no Ollama needed)
├── tools.py                        # deterministic data access + math — no AI
├── llm.py                          # the only file that talks to the model
├── state.py                        # shared agent memory schema
├── agent_nodes.py                  # the six agent steps
├── graph.py                        # wires the steps into a running LangGraph loop
├── scenario.py                     # injects a second disruption for the live demo
├── run_demo.py                     # two-act terminal demo
├── app.py                          # interactive Streamlit dashboard
├── requirements.txt
├── setup.bat / setup.sh            # one-command environment setup
├── README.md
└── ARCHITECTURE.md                 # full component-by-component documentation
```

## Quick Start

**1. Install [Ollama](https://ollama.com), then pull the model:**
```bash
ollama pull phi3:mini
```

**2. Set up the environment** (or just run `setup.bat` / `setup.sh`):
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

**3. Run the two-act terminal demo:**
```bash
python run_demo.py
```

**4. Or launch the interactive dashboard:**
```bash
streamlit run app.py
```

No accounts, API keys, or configuration required for any of the above.

## Sample Run (real output)



```
ACT 1: Handling the initial disruption
 - Monitoring inventory, shipments, and vendor data...
 - 5 disruptions detected. Prioritizing low_stock (urgency 0.55) over 4 other(s).
 - Retrieved 5 candidate vendor/route combinations for P002.
 - 1 of 5 plans satisfy all constraints.
 - Selected vendor Bharat Electro Components via road route.
 - Verification passed. Plan applied successfully.

Injecting a second, unrelated disruption...
[scenario] Webcam 1080p stock dropped from 200 to 10 (reorder threshold is 90)

ACT 2: Agent reacts to the new disruption
 - 5 disruptions detected. Prioritizing low_stock (urgency 0.889) over 4 other(s).
 - Retrieved 3 candidate vendor/route combinations for P006.
 - 2 of 3 plans satisfy all constraints.
 - Selected vendor Bharat Electro Components via road route.
 - Verification passed. Plan applied successfully.
```

Full decision logs, chosen plans, and LLM justifications for real recorded runs are browsable in the [live results viewer](https://supply-chain-xofybygvdqgg98qyxhwaco.streamlit.app/) — no install required.

## Deployment

The live agent requires a locally running LLM (Ollama), which cloud platforms like Streamlit Community Cloud can't host directly — this is a direct, deliberate consequence of the no-external-API design, not a limitation of the agent itself.

To make the system reproducible and viewable without local setup, this repo ships **two ways to experience it**:

| | What it is | Where |
|---|---|---|
| **Runnable (primary)** | The full live agent, reasoning in real time | `python run_demo.py` or `streamlit run app.py`, locally |
| **Deployed (companion)** | A read-only viewer replaying real recorded runs | [Live link](https://supply-chain-xofybygvdqgg98qyxhwaco.streamlit.app/) — deployed from `deployed_demo/` |

## Security

This repository contains **no API keys, passwords, tokens, or credentials of any kind** — the project has no external services to authenticate against, by design.

## Future Scope

- **True constrained optimization** — multi-vendor order splitting via `pulp`, instead of single-vendor picks
- **Policy-aware reasoning** — a lightweight retrieval layer over a real sustainability/sourcing policy document
- **Model upgrade path** — swap `phi3:mini` for a larger local model if higher-stakes reasoning is needed, with zero changes outside `llm.py`

---

*Built for Tech Zephyr 4.0 — Agentic AI Hackathon.*
