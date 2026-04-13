# AgentSwift: Efficient LLM Agent Design via Value-guided Hierarchical Search
> Paper: arXiv 2506.06017 | AAAI 2026
> Authors: Yu Li, Lehui Li, Zhihao Wu, Qingmin Liao, Jianye Hao, Kun Shao, Fengli Xu
> Read date: 2026-04-13

## TL;DR

Generalizes both AFlow (MCTS over workflow code) and AgentSquare (modular components) into a unified hierarchical search. Key innovation is a trained 7B value model that replaces expensive real evaluations, enabling uncertainty-guided MCTS with only 60 real evaluations total.

## Hierarchical Search Space

Two levels searched jointly:

### Level 1: Agentic Workflow (W)
Same as AFlow — nodes (LLM calls) connected by code edges. Operators: Ensemble, Judge, Review, Revise.

### Level 2: Functional Components
Same idea as AgentSquare's modules but composable (not locked into a fixed pipeline):
- **Memory (M)** = `(prompt, temperature, backend_db)` — retrieve/store context
- **Tool Use (T)** = `(prompt, temperature, toolset)` — call external APIs
- **Planning (P)** = `(prompt, temperature)` — task decomposition

Agent definition: `A = (W, M, T, P)` where `P ∈ S_planning` (Planning, NOT Prompt space)

**Notation overload warning**: calligraphic `P` = prompt space (in node definition `Ni = (Mi, Pi, τi, Fi)`), while bold `P` in agent tuple = Planning component. Two different things.

## Algorithm (Uncertainty-guided Hierarchical MCTS)

```
SETUP:
  Seed experience pool with known agents
  Train value model fθ on seed data (~220 labeled samples)

FOR each iteration (budget = 60):
  1. SELECTION:     Pick parent from pool, weighted by score + uncertainty
  2. RECOMBINATION: LLM swaps one module from pool → value model picks best of N
  3. MUTATION:      LLM writes new code for one module → value model picks best of N
  4. REFINEMENT:    LLM tweaks based on failure cases → value model picks best of N
  5. EVALUATION:    ONE real eval → compute uncertainty = |predicted - actual|
  6. BACKPROP:      Update pool with (agent, score, uncertainty)
```

Key: only **1 real evaluation per iteration** (60 total). Value model filters ~3×N candidates per iteration cheaply.

### Selection Formula
```
P(i) = λ · (1/n) + (1-λ) · softmax(α · ((1-β)·score + β·uncertainty - max))
```
Extends AFlow's selection by adding **uncertainty** — agents where the value model was wrong get explored more.

### Expansion: 3-Step Pipeline
Each step produces N candidates, value model picks the best, passes to next step:

1. **Recombination** — LLM proposes module swaps from existing pool (which module to swap is LLM's guess, no principled selection)
2. **Mutation** — LLM writes new module code (same IO interface, different logic)
3. **Refinement** — LLM makes fine-grained tweaks based on failure logs

## Value Model (Key Innovation)

- **Not** LLM few-shot prediction (AgentSquare's approach)
- A **fine-tuned 7B LM** (Mistral-7B or Qwen2.5-7B) trained via MSE loss
- Input: agent architecture description + task description → Output: predicted score
- R²=0.83, Spearman=0.90 — much better than GPT-4o few-shot (R²=0.48)
- Generalizes to unseen tasks with ~30 labeled examples via adapter tuning

### Training Data Construction
Two-stage process to build ~220 labeled samples:
1. **Pairwise covering arrays** — ensure all 2-way component interactions sampled
2. **Balanced Bayesian sampling** — GP surrogate with UCB (high-performing) + LCB (uncertain/low-performing) acquisition

### Uncertainty Loop
```
u = |s_predicted - s_real|
```
High uncertainty → value model was wrong → that agent's neighborhood gets higher selection priority next round. Self-correcting exploration.

## Discovered Module Examples

### Memory Mutations
| Module | Task | Retrieval | Storage |
|--------|------|-----------|---------|
| `ContextualGuidanceMemory` | ALFWorld | k=3 + LLM re-ranks by relevance score | Summarize key actions |
| `AdaptiveMemory` | MATH | k=2, just concatenate (no re-ranking) | Voyager-style ≤6 sentence summary |

ALFWorld needs smarter retrieval (diverse scenarios); MATH benefits from simpler retrieval (structurally similar problems).

### Planning Mutations
| Module | Task | Style |
|--------|------|-------|
| `ConciseClarityPlanning` | ALFWorld | Few-shot, tool-aware, "mirror examples precisely" |
| `AdaptiveHierarchicalPlanning` | MATH | Zero-shot, "minimal set of logical steps, each builds on previous" |

**Honest observation**: Planning "mutation" is really just prompt rewriting. The `PlanningBase` interface is just `create_prompt() → string`. No code-level variation — only the prompt text changes. Memory has more meaningful code variation (different retrieval strategies, re-ranking logic).

## Critical Observations

### Genuine improvements over prior work
- **Hierarchical search space** genuinely generalizes AFlow (workflow only) and AgentSquare (fixed pipeline)
- **Trained value model** is cheaper and more accurate than LLM-as-predictor
- **Uncertainty-guided selection** is principled (explore where model is least calibrated)
- **Only 60 real evals** vs AFlow's 20 iterations × 5 runs = 100, AgentSquare's ~$60/eval

### Still fundamentally LLM trial-and-error
- No gradient on any component
- Recombination: "which module to swap" is LLM's guess, no attribution
- Mutation: LLM writes new code with no signal about what specifically to improve
- Value model guides *which agents to try* but not *how to improve them*

### Planning module is weak
- Just prompt rewriting, not real code-level mutation
- The "hierarchical search over functional components" claim is strongest for Memory, weakest for Planning

## Comparison Table

| | ADAS | AFlow | AgentSquare | AgentSwift |
|---|---|---|---|---|
| **Workflow search** | Open code, linear | Open code, MCTS | Fixed 4-slot | Open code, MCTS |
| **Functional components** | No | No | Yes, fixed pipeline | Yes, composable |
| **Search algorithm** | LLM from flat list | MCTS | Evolve+recombine loop | Uncertainty-guided MCTS |
| **Performance predictor** | None | None | LLM few-shot | Trained 7B model |
| **Uncertainty** | No | No | No | Yes |
| **Real evals needed** | ~30 | ~100 (20×5) | ~15-18 | 60 |
| **Gradient** | No | No | No | No |

## Results

- 8.34% average gain over baselines across 7 benchmarks
- Steeper search trajectory (finds good agents faster)
- Model-agnostic: agents discovered with GPT-4o-mini transfer to DeepSeek-V3 and GPT-4o
- Value model generalizes to unseen tasks with ~30 labeled examples
