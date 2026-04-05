"""
Plot agent performance (fitness median) by generation for each benchmark.
Usage: python plot_performance.py
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


def parse_fitness(fitness_str):
    """Extract median, CI low, and CI high from fitness string."""
    median_match = re.search(r"Median:\s*([\d.]+)%", fitness_str)
    ci_match = re.search(r"\(([\d.]+)%,\s*([\d.]+)%\)", fitness_str)
    median = float(median_match.group(1)) if median_match else None
    ci_low = float(ci_match.group(1)) if ci_match else None
    ci_high = float(ci_match.group(2)) if ci_match else None
    return median, ci_low, ci_high


def load_benchmark(filepath):
    """Load agents and return list of (generation_index, median, ci_low, ci_high, name)."""
    with open(filepath, "r") as f:
        archive = json.load(f)

    agents = []
    for agent in archive:
        fitness_str = agent.get("fitness")
        if not fitness_str:
            continue
        median, ci_low, ci_high = parse_fitness(fitness_str)
        if median is None:
            continue

        gen = agent.get("generation", "initial")
        gen_idx = 0 if gen == "initial" else int(gen)
        agents.append((gen_idx, median, ci_low, ci_high, agent.get("name", "unknown")))

    # Sort by generation index
    agents.sort(key=lambda x: x[0])
    return agents


def plot_all_benchmarks():
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for idx, (benchmark, filename) in enumerate(RESULT_FILES.items()):
        filepath = os.path.join(RESULTS_DIR, filename)
        if not os.path.exists(filepath):
            continue

        agents = load_benchmark(filepath)
        gens = [a[0] for a in agents]
        medians = [a[1] for a in agents]
        ci_lows = [a[2] for a in agents]
        ci_highs = [a[3] for a in agents]
        names = [a[4] for a in agents]

        yerr_low = [max(0, m - lo) for m, lo in zip(medians, ci_lows)]
        yerr_high = [max(0, hi - m) for m, hi in zip(medians, ci_highs)]

        ax = axes[idx]
        ax.errorbar(gens, medians, yerr=[yerr_low, yerr_high],
                     fmt="o-", capsize=3, markersize=4, alpha=0.8, linewidth=1)

        # Highlight the best agent
        best_idx = max(range(len(medians)), key=lambda i: medians[i])
        ax.annotate(
            names[best_idx],
            xy=(gens[best_idx], medians[best_idx]),
            xytext=(10, 10), textcoords="offset points",
            fontsize=7, color="red",
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8),
        )
        ax.plot(gens[best_idx], medians[best_idx], "r*", markersize=12, zorder=5)

        ax.set_title(benchmark, fontsize=14, fontweight="bold")
        ax.set_xlabel("Generation")
        ax.set_ylabel("Fitness (Median %)")
        ax.grid(True, alpha=0.3)

    # Hide the unused 6th subplot
    axes[5].set_visible(False)

    fig.suptitle("Agent Performance by Generation (with 95% CI)", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig("agent_performance_by_generation.png", dpi=150, bbox_inches="tight")
    print("Saved: agent_performance_by_generation.png")
    plt.show()


if __name__ == "__main__":
    plot_all_benchmarks()
