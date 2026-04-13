# AFlow: Automating Agentic Workflow Generation
> Paper: arXiv 2410.10762 | ICLR 2025
> Authors: Jiayi Zhang et al.
> Read date: 2026-04-12

## TL;DR

Uses MCTS to search over Python code that chains multiple LLM calls. Each MCTS tree node is a complete workflow. An LLM optimizer rewrites the code each iteration, guided by textual logs of what worked/failed before.

## Key Idea

- Represent agentic workflows as Python code (a single `__call__` function)
- Use Monte Carlo Tree Search to find the best code variant
- LLM (Claude-3.5-Sonnet) acts as the optimizer that rewrites code each round

## Search Formulation

- **Search space**: $S_{\text{AFlow}} = \{(P_1, \ldots, P_n, E, O_1, \ldots, O_n)\}$
  - $P_i$: prompts at each node
  - $E$: code edges (Python control flow connecting nodes)
  - $O_i$: operators (predefined building blocks)
- **Objective**: $W^* = \arg\max_{W \in S} G(W, T)$
- They fix model, temperature, output format — only search over prompts, code edges, and operators

## MCTS Components

| Step | What happens |
|------|-------------|
| **Selection** | Pick a parent workflow via soft mixed probability (softmax over scores + uniform for exploration) |
| **Expansion** | LLM optimizer reads parent code + experience log, rewrites the code |
| **Evaluation** | Run new workflow 5x on validation set, compute mean score |
| **Backpropagation** | Log (modification, score, improved?) onto parent's experience |

Repeat for 20 rounds. Early stopping if top-k scores don't improve for 5 rounds.

## Operators (Predefined Building Blocks)

7 operators: Generate, Format, Review & Revise, Ensemble, Test, Programmer, Custom

These are just wrapper functions around LLM calls with specific prompt templates.

## Critical Observations

### Not actually "agentic"
- A workflow is a **single Python function** orchestrating multiple LLM API calls
- No multiple agents, no inter-agent communication, no agent autonomy
- The execution order is fully determined by Python code, not by agent decisions
- "Agentic" here just means "multiple LLM calls in one script"

### Node/edge distinction is blurry
- "Nodes" = LLM calls, "Edges" = the rest of the Python code
- But in implementation there's no `Edge` class — it's all one function
- The formulation $S = \{(N, E)\}$ suggests they're separable, but the LLM optimizer rewrites everything at once

### No real gradient or credit assignment
- "Backpropagation" is NOT gradient-based — it's just logging scores to the tree
- No per-component attribution: can't tell if improvement came from prompt change, operator swap, or control flow edit
- Optimization signal is a single scalar (task score) for the entire workflow
- The LLM optimizer does trial-and-error guided by natural language logs of past attempts
- No gradient on prompts, operators, or edges — just "you changed X, score went up/down, guess what to try next"

### Comparison to ADAS
- ADAS stores past workflows in a flat list; AFlow organizes them in a tree
- AFlow's tree structure lets the optimizer see which modifications led to improvements along each branch
- Both use code representation, but AFlow adds predefined operators for efficiency

## Results

- 5.7% average improvement over manually designed baselines across 6 benchmarks
- 19.5% over ADAS
- Enables smaller models (GPT-4o-mini) to outperform GPT-4o at 4.55% of the cost
- Works across QA (HotpotQA, DROP), code (HumanEval, MBPP), and math (GSM8K, MATH)
