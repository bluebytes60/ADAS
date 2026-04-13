# AgentSquare: Automatic LLM Agent Search in Modular Design Space
> Paper: arXiv 2410.06153 | ICLR 2025
> Authors: Yu Shang, Yu Li, Keyu Zhao, Likai Ma, Jiahe Liu, Fengli Xu, Yong Li
> Read date: 2026-04-13

## TL;DR

Decomposes LLM agents into 4 standardized modules (Planning, Reasoning, Tool Use, Memory), then searches over module combinations via LLM-driven evolution and recombination. The main contribution is the modular design space, not the search algorithm.

## The Four Modules

| Module | Input | Output | What it does |
|--------|-------|--------|-------------|
| **Planning** | task description + feedback | sub-task sequence | Decomposes complex tasks into steps |
| **Reasoning** | sub-task + tool instructions + feedback | solution | Core "thinking" — prompts LLM to solve each sub-task (CoT, ToT, Self-Refine, etc.) |
| **Tool Use** | problem from reasoning + tool pool | tool response | Selects and calls external tools when LLM knowledge is insufficient |
| **Memory** | current observation | retrieved experience | Read/write to memory database; stores and retrieves past observations |

Each module has a **standardized IO interface** — any implementation can be swapped in as long as it matches the interface.

## Workflow Structure

Fixed pipeline, never changes:
```
Task → Planning → [sub-tasks]
                      ↓
                 Reasoning ←→ Tool Use
                      ↕
                   Memory
                      ↓
                 Action → Environment → Feedback → back to Planning
```

## Search Algorithm

Simple alternating loop, **no tree search**:

```
For each iteration:
    1. Module Evolution   → LLM rewrites one module's code, real-test all 4 variants
    2. Module Recombination → LLM proposes N module swaps, predictor filters, pick best

Stop if no improvement for 5 consecutive iterations (~15-18 iterations total)
```

### Module Evolution
- LLM receives: task description, current module code, all modules in pool, experience pool
- LLM writes a **new Python class** with same IO interface but different logic
- Only **one module mutated at a time** → gives per-module credit assignment
- New modules get **real-tested** (expensive) since predictor has no data on them
- New modules added to the module pool for future recombination

### Module Recombination
- LLM proposes N candidates by swapping modules from the pool
- **Performance predictor** (another LLM) scores all N candidates cheaply
  - In-context few-shot: sees past (combination → score) pairs, predicts new score
  - Cost: ~0.025% of real evaluation
  - Only works for recombination (existing modules have data), not evolution (new code)
- Only top-scoring candidate moves forward

### Performance Predictor
- Used as a **filter** during recombination only
- LLM pattern-matches from experience table to guess scores
- Paper shows predicted vs actual scores correlate well (Figure 5)
- Saves significant cost on expensive interactive environments (~$60 per full eval on ALFWorld)

## Critical Observations

### Essentially random search with LLM heuristics
- No principled search algorithm (no MCTS, no tree, no selection policy)
- Just "LLM proposes, evaluate, repeat"
- Paper's own ablation: **random module search** already gets competitive results (0.620 vs AgentSquare's 0.695 on ALFWorld) — the gap isn't huge
- The real win is the modular design space itself, not the search

### Fixed workflow topology
- The 4-slot pipeline structure never changes
- Can only discover new module implementations, not new workflow structures
- Cannot find novel topologies like AFlow can (e.g., adding loops, conditionals)

### Per-module attribution (advantage over AFlow)
- Since only one module changes at a time, you know which module caused score change
- AFlow rewrites everything at once → no credit assignment

## Comparison: AgentSquare vs AFlow vs ADAS

| | ADAS | AFlow | AgentSquare |
|---|---|---|---|
| **Contribution** | Problem formulation | Real search algorithm (MCTS) | Modular design space |
| **Search space** | Open code | Open code | 4-slot Cartesian product |
| **Search method** | LLM proposes from flat list | MCTS with tree-structured experience | LLM evolve + recombine loop |
| **Structure** | Linear | Tree | Flat loop |
| **Credit assignment** | None | None (whole workflow score) | Per-module (one change at a time) |
| **Gradient** | No | No | No |
| **All three**: LLM trial-and-error with no real gradient on any component |

## Results

- 17.2% average improvement over best hand-crafted agents across 6 benchmarks
- Benchmarks cover web (Webshop), embodied (ALFWorld, SciWorld), tool use (M3Tool, TravelPlanner), game (PDDL)
- Discovered modules are interpretable and transferable
