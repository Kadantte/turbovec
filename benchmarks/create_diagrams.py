"""
Create benchmark comparison bar charts.

Generates:
  - arm_speed.png: ARM (M3 Max) search latency, TQ vs FAISS
  - x86_speed.png: x86 (Sapphire Rapids) search latency, TQ vs FAISS
"""

import matplotlib.pyplot as plt
import numpy as np

# ARM results (Apple M3 Max, median of 5 runs)
arm = {
    "d1536_2bit_st": {"tq": 1.391, "faiss": 1.234},
    "d1536_2bit_mt": {"tq": 0.131, "faiss": 0.128},
    "d1536_4bit_st": {"tq": 2.580, "faiss": 2.451},
    "d1536_4bit_mt": {"tq": 0.236, "faiss": 0.228},
    "d3072_2bit_st": {"tq": 3.002, "faiss": 2.451},
    "d3072_2bit_mt": {"tq": 0.328, "faiss": 0.224},
    "d3072_4bit_st": {"tq": 5.370, "faiss": 4.923},
    "d3072_4bit_mt": {"tq": 0.560, "faiss": 0.447},
}

# x86 results (Intel Sapphire Rapids, 4 vCPUs, median of 5 runs)
x86 = {
    "d1536_2bit_st": {"tq": 2.906, "faiss": 1.211},
    "d1536_2bit_mt": {"tq": 1.048, "faiss": 0.588},
    "d1536_4bit_st": {"tq": 4.447, "faiss": 2.489},
    "d1536_4bit_mt": {"tq": 1.666, "faiss": 1.174},
    "d3072_2bit_st": {"tq": 9.155, "faiss": 2.509},
    "d3072_2bit_mt": {"tq": 2.872, "faiss": 1.173},
    "d3072_4bit_st": {"tq": 12.409, "faiss": 5.039},
    "d3072_4bit_mt": {"tq": 4.138, "faiss": 2.338},
}


def make_chart(data, title, filename):
    configs_st = ["d1536_2bit_st", "d1536_4bit_st", "d3072_2bit_st", "d3072_4bit_st"]
    configs_mt = ["d1536_2bit_mt", "d1536_4bit_mt", "d3072_2bit_mt", "d3072_4bit_mt"]
    labels_st = ["d=1536\n2-bit", "d=1536\n4-bit", "d=3072\n2-bit", "d=3072\n4-bit"]
    labels_mt = labels_st

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Single-threaded
    x = np.arange(len(configs_st))
    w = 0.35
    tq_vals = [data[c]["tq"] for c in configs_st]
    faiss_vals = [data[c]["faiss"] for c in configs_st]
    bars1 = ax1.bar(x - w/2, tq_vals, w, label="TurboQuant", color="#4C72B0")
    bars2 = ax1.bar(x + w/2, faiss_vals, w, label="FAISS", color="#DD8452")
    ax1.set_ylabel("ms / query")
    ax1.set_title("Single-threaded")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels_st)
    ax1.legend()
    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                 f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                 f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8)

    # Multi-threaded
    tq_vals = [data[c]["tq"] for c in configs_mt]
    faiss_vals = [data[c]["faiss"] for c in configs_mt]
    bars1 = ax2.bar(x - w/2, tq_vals, w, label="TurboQuant", color="#4C72B0")
    bars2 = ax2.bar(x + w/2, faiss_vals, w, label="FAISS", color="#DD8452")
    ax2.set_ylabel("ms / query")
    ax2.set_title("Multi-threaded")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels_mt)
    ax2.legend()
    for bar in bars1:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                 f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=8)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved {filename}")


# Recall results (TQ vs FAISS)
recall = {
    "d1536_2bit": {
        "tq":    {"1": 0.870, "2": 0.961, "4": 0.998, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
        "faiss": {"1": 0.882, "2": 0.973, "4": 0.996, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
    },
    "d1536_4bit": {
        "tq":    {"1": 0.955, "2": 0.996, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
        "faiss": {"1": 0.956, "2": 0.998, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
    },
    "d3072_2bit": {
        "tq":    {"1": 0.912, "2": 0.986, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
        "faiss": {"1": 0.903, "2": 0.977, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
    },
    "d3072_4bit": {
        "tq":    {"1": 0.967, "2": 0.997, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
        "faiss": {"1": 0.967, "2": 0.998, "4": 1.000, "8": 1.000, "16": 1.000, "32": 1.000, "64": 1.000},
    },
}


def make_recall_chart(data, filename):
    ks_str = ["1", "2", "4", "8", "16"]
    ks_int = [1, 2, 4, 8, 16]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for ax, dim, title in [(ax1, "d1536", "d=1536"), (ax2, "d3072", "d=3072")]:
        for bw, ls_tq, ls_f, marker_tq, marker_f in [("2bit", "-", "--", "o", "s"), ("4bit", "-", "--", "^", "D")]:
            config = f"{dim}_{bw}"
            tq_vals = [data[config]["tq"][k] for k in ks_str]
            faiss_vals = [data[config]["faiss"][k] for k in ks_str]
            bw_label = bw.replace("bit", "-bit")
            ax.plot(ks_int, tq_vals, f"{marker_tq}{ls_tq}", label=f"TQ {bw_label}", color="#4C72B0" if bw == "2bit" else "#55A868", linewidth=2, markersize=6)
            ax.plot(ks_int, faiss_vals, f"{marker_f}{ls_f}", label=f"FAISS {bw_label}", color="#DD8452" if bw == "2bit" else "#C44E52", linewidth=2, markersize=6)

        ax.set_title(title)
        ax.set_xlabel("k")
        ax.set_xscale("log", base=2)
        ax.set_xticks(ks_int)
        ax.set_xticklabels(ks_str)
        ax.set_ylim(0.85, 1.005)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

    ax1.set_ylabel("recall@1@k")
    fig.suptitle("Recall — TurboQuant vs FAISS (100K vectors, k=64 search)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved {filename}")


def make_compression_chart(filename):
    datasets = ["GloVe\nd=200", "OpenAI\nd=1536", "OpenAI\nd=3072"]
    fp32 = [76.3, 585.9, 1171.9]
    two_bit = [5.1, 37.0, 73.6]
    four_bit = [9.9, 73.6, 146.9]

    x = np.arange(len(datasets))
    w = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w, fp32, w, label="FP32", color="#C44E52")
    ax.bar(x, four_bit, w, label="4-bit", color="#DD8452")
    ax.bar(x + w, two_bit, w, label="2-bit", color="#4C72B0")

    for i in range(len(datasets)):
        ax.text(x[i] - w, fp32[i] + 15, f"{fp32[i]:.0f}", ha="center", fontsize=9)
        ax.text(x[i], four_bit[i] + 15, f"{four_bit[i]:.0f}", ha="center", fontsize=9)
        ax.text(x[i] + w, two_bit[i] + 15, f"{two_bit[i]:.0f}", ha="center", fontsize=9)

    ax.set_ylabel("Index size (MB)")
    ax.set_title("Index Size — 100K vectors", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Saved {filename}")


if __name__ == "__main__":
    import os
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    make_chart(arm, "Search Latency — ARM (Apple M3 Max)", os.path.join(out_dir, "arm_speed.png"))
    make_chart(x86, "Search Latency — x86 (Intel Sapphire Rapids, 4 vCPU)", os.path.join(out_dir, "x86_speed.png"))
    make_recall_chart(recall, os.path.join(out_dir, "recall.png"))
    make_compression_chart(os.path.join(out_dir, "compression.png"))
