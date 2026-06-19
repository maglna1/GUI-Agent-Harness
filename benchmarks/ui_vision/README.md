# UI-Vision — GUI Grounding Benchmark

UI-Vision is a large-scale GUI element grounding benchmark with 5,479 samples across three splits: basic, functional, and spatial reasoning.

- Model: **GPT-5.5** (openai-codex)
- Samples: **5,479 / 5,479** ✅
- Pipeline: **single-shot Phase-3** (`find_target_in_known` — one LLM call over
  the component list + full screenshot). NOT the iterative-zoom locator,
  despite what this header used to claim: the recorded rows carry only
  `listed_entry`/`direct_pixel` grounding types and component-memory phase
  timings, with zero zoom traces — the `app_name` routing gate never fired in
  that run. Treat 68.64% as the weak-path baseline, not the locator's score.
- Accuracy: **68.64%** (3,761 correct / 1,718 wrong / 0 WF)

---

## Optimized pipeline — FULL re-run (2026-06-20, all 5,479 samples)

The single-shot 68.64% above is the weak-path baseline (it never entered the
locator). Re-running every sample through the iterative-zoom locator
(`configs/ui_vision_gpt_zoom.yaml`, GPT-5.5) — same rows compared against the
old single-shot run:

| Split | Samples | Old (single-shot) | **Optimized (zoom)** | Δ (same-question) |
|-------|---------|-------------------|----------------------|-------------------|
| Basic | 1,772 | 73.1% | **78.3%** | +5.2 |
| Functional | 1,772 | 67.0% | **72.9%** | +5.9 |
| Spatial | 1,935 | 66.0% | **72.1%** | +6.0 |
| **Total** | **5,479** | **68.64%** | **74.4%** | **+5.7** |

0 error rows. This is the full-benchmark number (the earlier 300-sample
stratified slice predicted ~76%, consistent within sampling noise; on that
slice an added disagreement-judge + identity-verify ensemble reached 78.3% /
80.0% corrected, but the ensemble was found net-negative on ScreenSpot-Pro and
is not part of the headline full-run config — see the experiment log).

Method = iterative-zoom locator alone (the SSPro "best" config + `element`
convention + `keep_best` fallback). Cross-model datapoint, same config + same
benchmark: GPT-5.5 88.7% vs MiniMax-M3 47.4% on ScreenSpot-Pro — the scaffold
amplifies a strong backbone but cannot rescue a weak one. SSPro regression
guard: easy100 × legacy config = 98/100 (no regression). Full experiment
history (21+ ablations incl. refuted ideas):
`../screenspot_pro/UI_VISION_OPTIMIZATION_LOG.md` ·
results: `../screenspot_pro/results/FULL_RERUN_RESULTS.md`

## Results (legacy single-shot full run)

| Model | Progress | Correct | Wrong | WF | Accuracy | Status |
|-------|----------|---------|-------|-----|----------|--------|
| **GPT-5.5** | 5479/5479 | 3761 | 1718 | 0 | **68.64%** | ✅ Done |

## By Split

| Split | Samples | Correct | Accuracy |
|-------|---------|---------|----------|
| Basic | 1772 | 1295 | **73.1%** |
| Functional | 1772 | 1188 | **67.0%** |
| Spatial | 1935 | 1278 | **66.0%** |
| **Total** | **5479** | **3761** | **68.64%** |

> Spatial reasoning questions are significantly harder: the model must identify "the button to the right of X" or "the element above Y" — requiring spatial relationship understanding beyond simple element recognition.

## Files
- `../screenspot_pro/results/ui_vision_gpt_5_5/full_report.md` — summary report
- `../screenspot_pro/results/ui_vision_gpt_5_5/full_summary.json` — aggregated stats by split
- `../screenspot_pro/results/ui_vision_gpt_5_5/results.jsonl` — 5,479 per-sample records
