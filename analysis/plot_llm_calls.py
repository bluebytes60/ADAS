"""
Plot estimated LLM calls per question by generation for each benchmark.
Usage: python plot_llm_calls.py
"""

import json
import os
import re
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
RESULT_FILES = {
    "MMLU": "mmlu_gpt3.5_results.json",
    "MGSM": "mgsm_gpt3.5_results.json",
    "DROP": "drop_gpt3.5_results.json",
    "GPQA": "gpqa_gpt3.5_results.json",
    "ARC": "arc_gpt3.5_results.json",
}


def count_llm_calls(code_str):
    """
    Estimate the number of LLM calls per question from agent code.

    Counts direct agent invocations and attempts to detect loops that multiply calls.
    Returns the estimated call count.
    """
    if not code_str:
        return 0

    # Count direct agent calls: agent(...) patterns excluding definitions/instantiations
    # Look for patterns like: agent([ or agent_name([
    call_patterns = re.findall(
        r'(?:agent|_agent)\s*\(\s*\[', code_str
    )
    direct_calls = len(call_patterns)

    # Also count calls like: agents[i]([ or agents[idx]([
    indexed_calls = re.findall(r'agents?\[\w+\]\s*\(\s*\[', code_str)
    direct_calls += len(indexed_calls)

    if direct_calls == 0:
        # Fallback: count any pattern that looks like calling an LLMAgentBase instance
        fallback = re.findall(r'\w+_agent\w*\s*\(', code_str)
        direct_calls = len(fallback)

    # Try to detect loop multipliers
    # Look for "for ... in range(N)" where N is a number
    loop_matches = re.findall(r'for\s+\w+\s+in\s+range\(\s*(\d+)\s*\)', code_str)

    # Look for "for ... in range(variable)" and try to find the variable value
    var_loops = re.findall(r'for\s+\w+\s+in\s+range\(\s*([A-Za-z_]\w*)\s*\)', code_str)
    for var in var_loops:
        var_match = re.search(rf'{var}\s*=\s*(\d+)', code_str)
        if var_match:
            loop_matches.append(var_match.group(1))

    # Look for "for ... in range(len(...))" patterns
    len_loops = re.findall(r'for\s+\w+\s+in\s+range\(\s*len\(\s*(\w+)\s*\)\s*\)', code_str)
    for var in len_loops:
        # Try to find list size from list comprehension or explicit list
        list_match = re.search(rf'{var}\s*=\s*\[.*?for\s+\w+\s+in\s+(\[.*?\])', code_str)
        if list_match:
            items = list_match.group(1).count(',') + 1
            loop_matches.append(str(items))

    # Simple heuristic: if there are loops, check how many calls are inside them
    # by looking at indentation
    lines = code_str.split('\n')
    in_loop = False
    loop_depth_calls = 0
    non_loop_calls = 0
    current_loop_multiplier = 1

    for line in lines:
        stripped = line.strip()
        # Detect loop start
        loop_start = re.match(r'for\s+\w+\s+in\s+range\(', stripped)
        if loop_start:
            in_loop = True
            # Try to extract the range value
            range_match = re.search(r'range\(\s*(\d+)\s*\)', stripped)
            if range_match:
                current_loop_multiplier = int(range_match.group(1))
            else:
                var_match = re.search(r'range\(\s*(\w+)\s*\)', stripped)
                if var_match:
                    val = re.search(rf'{var_match.group(1)}\s*=\s*(\d+)', code_str)
                    if val:
                        current_loop_multiplier = int(val.group(1))
                    else:
                        current_loop_multiplier = 3  # default estimate
                else:
                    current_loop_multiplier = 3
            continue

        # Check if line has an agent call
        has_call = bool(re.search(r'(?:agent|_agent)\s*\(\s*\[', stripped) or
                        re.search(r'agents?\[\w+\]\s*\(\s*\[', stripped))

        if has_call:
            if in_loop:
                loop_depth_calls += current_loop_multiplier
            else:
                non_loop_calls += 1

    total = loop_depth_calls + non_loop_calls
    # If our line-by-line analysis found something, use it; otherwise fall back to simple count
    return total if total > 0 else direct_calls


def load_benchmark_calls(filepath):
    """Load agents and return list of (generation_index, llm_calls, name)."""
    with open(filepath, "r") as f:
        archive = json.load(f)

    agents = []
    for agent in archive:
        code = agent.get("code", "")
        calls = count_llm_calls(code)

        gen = agent.get("generation", "initial")
        gen_idx = 0 if gen == "initial" else int(gen)
        agents.append((gen_idx, calls, agent.get("name", "unknown")))

    agents.sort(key=lambda x: x[0])
    return agents


def plot_all_benchmarks():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for idx, (benchmark, filename) in enumerate(RESULT_FILES.items()):
        filepath = os.path.join(RESULTS_DIR, filename)
        if not os.path.exists(filepath):
            continue

        agents = load_benchmark_calls(filepath)
        gens = [a[0] for a in agents]
        calls = [a[1] for a in agents]
        names = [a[2] for a in agents]

        ax = axes[idx]
        ax.bar(range(len(agents)), calls, color="steelblue", alpha=0.7, edgecolor="navy", linewidth=0.5)

        # Label x-axis with generation numbers
        ax.set_xticks(range(len(agents)))
        ax.set_xticklabels([str(g) for g in gens], fontsize=6, rotation=45)

        # Highlight the agent with most calls
        max_idx = max(range(len(calls)), key=lambda i: calls[i])
        ax.bar(max_idx, calls[max_idx], color="tomato", alpha=0.8, edgecolor="darkred", linewidth=0.5)
        ax.annotate(
            f"{names[max_idx]}\n({calls[max_idx]} calls)",
            xy=(max_idx, calls[max_idx]),
            xytext=(10, 10), textcoords="offset points",
            fontsize=6, color="red",
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8),
        )

        ax.set_title(benchmark, fontsize=14, fontweight="bold")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Estimated LLM Calls / Question")
        ax.grid(True, alpha=0.3, axis="y")

    axes[5].set_visible(False)

    fig.suptitle("Estimated LLM Calls per Question by Generation", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig("agent_llm_calls_by_generation.png", dpi=150, bbox_inches="tight")
    print("Saved: agent_llm_calls_by_generation.png")
    plt.show()


if __name__ == "__main__":
    plot_all_benchmarks()
