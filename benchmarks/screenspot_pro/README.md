# ScreenSpot-Pro Benchmark

ScreenSpot-Pro is a GUI element grounding benchmark covering 1,581 professional
software samples across 5 subsets and 23 applications.

## Results Summary

| Model | Progress | Correct | Wrong | WF | Accuracy | Pipeline | Status |
|-------|----------|---------|-------|----|----------|----------|--------|
| **GPT-5.5** | 1581/1581 | 1390 | 191 | 0 | **87.9%** | legacy (fill/legacy, 8 rounds) | ✅ Done |
| Claude Opus 4.7 | 338/1581 | 267 | 71 | 1243 | 79.0%* | legacy | ⏹ Quota exhausted |
| Claude Opus 4.7 (stratified) | 78/1581 | 62 | 16 | 0 | 79.5% | — | ✅ Done |
| Claude Opus 4.8 (stratified) | 78/1581 | — | — | — | — | — | ✅ Done |

*Claude 4.7 full run: quota exhaustion caused 1,243 WF (infra failures, not model mistakes).

## GPT-5.5 by Subset

| Subset | Samples | Correct | Accuracy |
|--------|---------|---------|----------|
| Office | 230 | 221 | 96.1% |
| Development | 289 | 259 | 89.6% |
| Operating Systems | 196 | 177 | 90.3% |
| CAD | 306 | 259 | 84.6% |
| Creative | 306 | 259 | 84.6% |
| Scientific | 254 | 215 | 84.6% |
| **Total** | **1581** | **1390** | **87.9%** |

## GPT-5.5 Top/Bottom Apps

| App | Subset | Samples | Accuracy |
|-----|--------|---------|----------|
| EViews | Scientific | 50 | 98.0% |
| Word | Office | 84 | 97.6% |
| VMware | Development | 41 | 97.6% |
| Excel | Office | 64 | 96.9% |
| macOS | OS | 65 | 95.4% |
| ... | ... | ... | ... |
| Origin | Scientific | 62 | 58.1% |
| AutoCAD | CAD | 34 | 70.6% |
| FL Studio | Creative | 57 | 75.4% |
| Quartus | CAD | 45 | 75.6% |

## Tracked Code

- `run_screenspot_pro.py` — runs ScreenSpot-style annotation files
- `sync_full_final.py` — merges multiple runs into one canonical result directory
- `report_full_final.py` — prints a compact final/progress report
- `prepare_screenspot_versions.py` / `start_screenspot_versions.py` / `report_screenspot_versions.py` — ScreenSpot v1/v2 toolchain
- `prepare_gui_grounding_datasets.py` / `start_gui_grounding_datasets.py` / `report_gui_grounding_datasets.py` — UI-Vision / MMBench-GUI L2 toolchain
- `configs/` — pipeline configs (`main_baseline.yaml` = legacy, `known_good.yaml` = new)

## Files
- `results/gpt_5_5/full_report.md` — summary report
- `results/gpt_5_5/full_summary.json` — aggregated stats by subset/app
- `results/gpt_5_5/results.jsonl` — 1,581 per-sample records
