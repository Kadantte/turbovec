#!/usr/bin/env python3
"""Recall benchmark: OpenAI d=1536, 2-bit (TQ vs FAISS PQ)."""
import os, json, time, numpy as np, faiss
from turbovec import TurboQuantIndex

DATA_DIR = os.path.expanduser("~/data/py-turboquant")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
DIM = 1536
BIT_WIDTH = 2
K = 64
K_VALUES = [1, 2, 4, 8, 16, 32, 64]


def load_openai(dim, seed=42):
    path = os.path.join(DATA_DIR, f"openai-{dim}.npy")
    all_vecs = np.load(path)
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(all_vecs))
    database = all_vecs[idx[:100_000]]
    queries = all_vecs[idx[100_000:101_000]]
    database /= np.linalg.norm(database, axis=-1, keepdims=True)
    queries /= np.linalg.norm(queries, axis=-1, keepdims=True)
    return database, queries


def recall_at_1_at_k(true_top1, predicted_indices, k):
    return np.mean([true_top1[i] in predicted_indices[i, :k] for i in range(len(true_top1))])


def main():
    print(f"=== OpenAI d={DIM} {BIT_WIDTH}-bit ===")
    database, queries = load_openai(DIM)
    print(f"Database: {database.shape}, Queries: {queries.shape}")

    # Brute-force ground truth
    true_top1 = np.argmax(queries @ database.T, axis=1)

    # TurboQuant
    print("Building TQ index...")
    t0 = time.time()
    index_tq = TurboQuantIndex(DIM, bit_width=BIT_WIDTH)
    index_tq.add(database)
    print(f"TQ build: {time.time() - t0:.2f}s")

    t0 = time.time()
    _, tq_indices = index_tq.search(queries, k=K)
    print(f"TQ search: {time.time() - t0:.2f}s")

    tq_indices = np.array(tq_indices)
    tq_recalls = {str(k): round(recall_at_1_at_k(true_top1, tq_indices, k), 4) for k in K_VALUES}

    # FAISS PQ (2-bit equivalent: m=dim//2, nbits=4)
    m = DIM // 2
    print(f"Building FAISS PQ index (m={m}, nbits=4)...")
    t0 = time.time()
    index_faiss = faiss.IndexPQFastScan(DIM, m, 4)
    index_faiss.train(database)
    index_faiss.add(database)
    print(f"FAISS build: {time.time() - t0:.2f}s")

    t0 = time.time()
    _, faiss_ids = index_faiss.search(queries, K)
    print(f"FAISS search: {time.time() - t0:.2f}s")

    faiss_recalls = {str(k): round(recall_at_1_at_k(true_top1, faiss_ids, k), 4) for k in K_VALUES}

    results = {
        "dataset": f"openai-{DIM}",
        "dim": DIM,
        "bit_width": BIT_WIDTH,
        "tq_recalls": tq_recalls,
        "faiss_recalls": faiss_recalls,
    }

    print("\nTQ recalls:", tq_recalls)
    print("FAISS recalls:", faiss_recalls)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "recall_d1536_2bit.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
