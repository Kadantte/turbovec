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
- **Verdict: WIN** — committed (b635e1b).
- Post-hoc ST verification (after the objective grew _st cells): x86_st insert
  3153.8 vs 3153.1 baseline (parity — 1-thread pool takes the chunked path at
  serial speed), arm_st insert 1556 vs 1829 (faster). No single-core tax.

### Harness change (not a hypothesis)

Ryan's directive mid-run: ops must be optimized for both multicore and
single-core. Added `--st` mode (RAYON_NUM_THREADS=1) → 24 cells total
({arm,x86,arm_st,x86_st} × 6 ops). ST baselines pinned with pre-H1 core.
A win now requires the target op's 4-cell HM > x1.01 with no target cell
regressing. Full `cargo test -p turbovec` re-run after H1: all green (one
earlier transient 2-failure in a 4-test binary did not reproduce — watching).

### H2 — LUT-based seq_to_packed inner loop (target: insert)

After H1 the remaining first-mutation cost is per-row bit-by-bit unpacking:
~8 conditional bit-ORs per group byte. Replace with a 256-entry LUT mapping
each group byte to per-plane bit fields, assembling each plane byte from its
8/codes_per_byte group bytes. Helps ST directly and MT (same work per chunk).
Added bits=3 cases to the seq_to_packed round-trip test (was 2/4-bit only).

- Smoke (5 reps): insert x60.7/x31.2/x16.9/x9.2 (arm/x86/arm_st/x86_st). PASS.
- Soak (15 reps): insert x65.8 / x31.3 / x16.9 / x9.2 — target HM x18.67;
  delete rides to x19.8 / x13.1 / x12.0 / x6.8. WHM x1.63.
- Flags (search-arm x0.954, save-arm x0.588, save-arm_st x0.636, load-x86_st
  x0.965, load_search-arm_st x0.884) all cleared by interleaved H1-vs-H2 A/B:
  search/load_search identical across cores; save degrades monotonically on
  the Mac REGARDLESS of core (h1: 121→187 ms across rounds, h2: 120→250;
  x86 save stable ~390 throughout) — session-long SSD write-path drift, not
  code. NOTE for future save hypotheses: ARM save cell needs fresh machine
  state / cooldown; judge save primarily on x86 + A/B.
- Correctness: cargo test -p turbovec --lib green (42), round-trip incl. new
  bits=3 cases.
- **Verdict: WIN** — committed (13e3023).

### Machine-state incident (between H2 and H3)

ARM save cells ballooned to 450/1152 ms mid-session. Cause: every bench run
leaked a 77 MB `out.tvim` in a fresh mkdtemp dir — ~89 dirs ≈ 7 GB, root disk
down to 1.5 GiB free, SSD write path collapsing. Cleaned local + x86 temp dirs
(disk back to 5.9 GiB) and fixed bench_ops.py to use TemporaryDirectory (auto
cleanup). Consequence: the Mac's absolute numbers drift within a session —
ARM verdicts rely on interleaved A/B per the noise-band protocol.

### H3 — fused top-k + NEON block-max prune in ARM batch search (target: search)

The ARM batch path materialized a 3.2 MB score matrix per query-quad
(NEG_INFINITY fill + kernel store + branchy 200k-element rescan per query).
Fold each scored block straight into per-query heaps (same visit order and
rescan_min tie-break → bitwise-identical results), with a whole-block NEON
max prune once the heap is full — the ARM analogue of the existing x86
avx2_post_flush_heap_update design.

- Correctness: all 20 test binaries green; bitwise parity vs H2 wheel on
  random data with duplicate-row ties, mask, and single-query paths.
- Interleaved A/B (3 rounds, 11 reps each, both cores same machine state):
  search-arm_st 197.7 → 187.8 ms (x1.052 all rounds), search-arm 23.23 →
  22.69 (x1.024). x86 cells untouched by construction (cfg(aarch64)) and
  verified flat (67.17 vs 67.0 baseline).
- Target HM (x1.024, x1.052, x1.0, x1.0) = x1.019 > x1.01, no target cell
  regressing. Raw-vs-baseline search-arm reads x0.97 due to the documented
  Mac drift; A/B is authoritative per protocol.
- **Verdict: WIN** — committed.
