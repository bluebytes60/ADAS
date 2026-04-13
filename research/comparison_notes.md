# Comparison: ADAS vs AFlow vs AgentSquare vs AgentSwift
> Last updated: 2026-04-13
> Context: All four papers address automated design of agentic systems. ADAS defined the problem; the others build on it.

## What They Search Over

| | ADAS | AFlow | AgentSquare | AgentSwift |
|---|---|---|---|---|
| **Search space** | Open code (anything) | Open code (workflow) | 4 fixed slots (P/R/T/M) | Workflow + 3 composable components (M/T/P) |
| **Representation** | Entire agent as code | `__call__` function with operators | 4 Python classes with standard IO | Workflow code + component classes |
| **Workflow structure** | Free-form | Free-form | Fixed pipeline | Free-form |
| **Functional components** | No | No | Yes (rigid) | Yes (composable) |
| **Expressiveness** | Highest (anything goes) | High (any code flow) | Lowest (fixed topology) | High (workflow + components) |

ADAS and AFlow search open code but ignore functional components. AgentSquare has components but locked into a rigid pipeline. AgentSwift combines both — open workflow + plug-and-play components.

## How They Search

| | ADAS | AFlow | AgentSquare | AgentSwift |
|---|---|---|---|---|
| **Algorithm** | Linear list + LLM proposes | MCTS | Evolve/recombine loop | Uncertainty-guided MCTS |
| **Experience structure** | Flat list | Tree | Flat experience pool | Tree + uncertainty |
| **Exploration strategy** | LLM reads full history | Softmax selection + uniform | LLM reasons over pool | Softmax + uncertainty weighting |
| **Expansion** | LLM rewrites everything | LLM rewrites everything | 1 module at a time | 3-step: recombine → mutate → refine |
| **Credit assignment** | None | None | Per-module (1 swap at a time) | Partial (3-step pipeline, value model filters) |

ADAS is the simplest — just "here's what we tried, write something better." AFlow adds tree structure so the LLM sees branch-specific history. AgentSquare isolates module changes for attribution. AgentSwift combines MCTS tree + per-component changes + uncertainty for exploration.

## How They Evaluate

| | ADAS | AFlow | AgentSquare | AgentSwift |
|---|---|---|---|---|
| **Evaluation** | Real test | Real test (5× for robustness) | Real test + LLM predictor | Real test + trained 7B value model |
| **Predictor** | None | None | GPT-4o few-shot (R²≈0.48) | Fine-tuned 7B LM (R²≈0.83) |
| **Real evals needed** | ~30 | ~100 (20 iters × 5 runs) | 15-18 real + predictor filters | 60 real (1 per iteration) |
| **Cost per eval** | Low (reasoning tasks) | Low (reasoning tasks) | High (~$60 on ALFWorld) | High but reduced by predictor |
| **Uncertainty feedback** | No | No | No | Yes (\|predicted - actual\|) |

AFlow's 5× repeated evaluation is expensive but gives stable signal. AgentSquare introduced LLM-as-predictor to save cost. AgentSwift's trained value model is far more accurate and feeds uncertainty back into search.

## What Actually Changes During Search

| | ADAS | AFlow | AgentSquare | AgentSwift |
|---|---|---|---|---|
| **Prompts** | Yes | Yes | Yes | Yes |
| **Code control flow** | Yes | Yes | No (fixed pipeline) | Yes |
| **Operators/modules** | Implicit | Add/remove operators | Swap module implementations | Swap + write new modules |
| **Planning/Memory/Tools** | Only if LLM invents them | Only if LLM invents them | Explicit search dimension | Explicit search dimension |

## The Fundamental Limitation They All Share

**None of them have gradient.** Every single one works like this:

```
1. LLM proposes a change (guess)
2. Run it → get a score (black-box)
3. Tell LLM "that scored X" (text feedback)
4. LLM proposes next change (another guess)
```

The "optimization signal" is always a single scalar for the whole agent. No method can answer: "the prompt in node 3 is bad" or "the memory retrieval strategy is the bottleneck." They differ in how smartly they organize their guesses:

- **ADAS**: dumbest — flat list, no structure
- **AFlow**: smarter — tree tracks which modification paths worked
- **AgentSquare**: different angle — isolate modules for attribution, but random-ish search
- **AgentSwift**: smartest — tree + uncertainty + trained predictor, but still guessing

## What Each Paper Actually Contributed

| Paper | Real contribution | Search algorithm quality |
|-------|------------------|------------------------|
| **ADAS** | **Problem formulation** — defined "automated design of agentic systems" as a research area | Minimal (linear search) |
| **AFlow** | **Search algorithm** — first principled search (MCTS) over agent code | Best search structure among the four |
| **AgentSquare** | **Design space** — modular decomposition into P/R/T/M with standard IO | Weak (basically random + LLM heuristic) |
| **AgentSwift** | **Evaluation efficiency** — trained value model + uncertainty-guided exploration | Most complete system, but incremental over each predecessor |

## Evolution of Ideas

```
ADAS (2024)
├── Defined the problem: "search over agent code"
├── Linear search, no components, no predictor
│
├──→ AFlow (ICLR 2025)
│    └── Better search: MCTS over code
│        Still no components, no predictor
│
├──→ AgentSquare (ICLR 2025)
│    └── Better design space: 4 modular slots
│        Weak search, LLM predictor (noisy)
│
└──→ AgentSwift (AAAI 2026)
     └── Combines both:
         ├── AFlow's MCTS + open workflow
         ├── AgentSquare's functional components (made composable)
         └── New: trained value model + uncertainty
```

AgentSwift is the most complete but also the most incremental — each piece comes from a predecessor.

## Open Question

**Can we get actual gradients on agent design?** All four methods are fundamentally black-box optimization with LLM as proposer. The value model in AgentSwift is the closest to a differentiable signal, but it's only used for filtering candidates — not for computing gradients that tell you *how* to improve a specific module.
