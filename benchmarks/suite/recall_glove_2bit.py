#!/usr/bin/env python3
"""Recall benchmark: GloVe d=200, 2-bit (TQ only)."""
import os, json, time, numpy as np, h5py
from turbovec import TurboQuantIndex

DATA_DIR = os.path.expanduser("~/data/py-turboquant")
GLOVE_PATH = os.path.join(DATA_DIR, "glove-200-angular.hdf5")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
DIM = 200
BIT_WIDTH = 2
K = 64
K_VALUES = [1, 2, 4, 8, 16, 32, 64]


def load_glove(seed=42):
    f = h5py.File(GLOVE_PATH, "r")
    all_train = f["train"][:].astype(np.float32)
    queries = f["test"][:].astype(np.float32)
    rng = np.random.RandomState(seed)
    idx = rng.choice(len(all_train), 100_000, replace=False)
    database = all_train[idx]
    database /= np.linalg.norm(database, axis=-1, keepdims=True)
    queries /= np.linalg.norm(queries, axis=-1, keepdims=True)
    return database, queries


def recall_at_1_at_k(true_top1, predicted_indices, k):
    return np.mean([true_top1[i] in predicted_indices[i, :k] for i in range(len(true_top1))])


def main():
    print(f"=== GloVe d={DIM} {BIT_WIDTH}-bit ===")
    database, queries = load_glove()
    print(f"Database: {database.shape}, Queries: {queries.shape}")

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

    results = {
        "dataset": "glove",
        "dim": DIM,
        "bit_width": BIT_WIDTH,
        "tq_recalls": tq_recalls,
        "faiss_recalls": None,
    }

    print("\nTQ recalls:", tq_recalls)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "recall_glove_2bit.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
