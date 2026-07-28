# Six-op hill-climb — results log

Objective: WHM of 12 per-cell speedups vs `benchmarks/results/hillclimb_baseline.json`
(weights search 3, insert 2, delete 2, save 1, load 1, load_search 0 — gate-only).
Win = target op HM(arm,x86) > x1.01, no target cell regressing, all other cells
within 3% noise, correctness + durability floor never traded. Stop: 20 consecutive
non-wins.

Bench: `benchmarks/hillclimb/bench_ops.py` (N=200k, dim=768, 4-bit). Smoke = 5 reps
both arches; soak = 15 reps. x86 = GCP c3-standard-8 (Sapphire Rapids).

Non-win streak: 0

## Baseline

Pinned in `benchmarks/results/hillclimb_baseline.json` (15 reps/arch, core = main
b8328d4). Measured noise, established by interleaved old/new A/B runs during H1:
ARM save ±20%, ARM load ±40%, x86 search bimodal (67–117 ms band under neighbor
noise), x86 load ±30%. The 3% gate in whm.py is the *systematic* bar; apparent
cell moves inside these bands need an interleaved A/B before they count as real
regressions.

## Hypotheses

### H1 — parallelize `seq_to_packed` (target: insert)

The first mutation after a v6 load materializes `packed_codes` from the blocked
cache via `pack::seq_to_packed`, a scalar single-threaded loop — 1.7 s ARM /
3.1 s x86 of the insert cell's total, and the same cost opens the delete cell.
Rows are independent → rayon over block-aligned row chunks, serial below 4 MB
(same threshold as `interleave_blocks_x86_in_place`).

- Smoke (5 reps): insert-arm 1649→160 ms, delete-arm 1725→224; insert-x86
  3128→569, delete-x86 3278→715. PASS.
- Soak (15 reps): insert x10.39 (arm) / x5.02 (x86), delete x7.91 / x4.27;
  target HM x6.77, WHM x1.53. whm.py flagged search-x86 x0.945, save-arm x0.727,
  load-x86 x0.774, load_search-arm x0.949 — all cleared by interleaved old/new
  A/B on both arches (no systematic difference; see noise bands above).
- Correctness: full `cargo test -p turbovec --lib` + io_v6 + io_hardening green;
  seq_to_packed round-trip covered by existing pack tests.
- **Verdict: WIN** — committed.
