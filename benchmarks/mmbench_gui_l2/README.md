# MMBench-GUI-L2 — GUI Element Grounding

Multi-platform GUI element grounding benchmark covering 6 platforms (Android/iOS/Linux/macOS/Web/Windows).

- Model: **GPT-5.5** (openai-codex)
- Samples: **3,594 / 3,594** (100%) ✅
- Pipeline: iterative_zoom (8 rounds), legacy (main_baseline.yaml)
- Accuracy: **91.52%** (3,271 correct / 303 wrong / 20 WF)

---

## Results

| Model | Progress | Correct | Wrong | WF | Accuracy | Status |
|-------|----------|---------|-------|-----|----------|--------|
| **GPT-5.5 (Ours)** | 3594/3594 | 3271 | 303 | 20 | **91.52%** | ✅ Done |

## L2 GUI Element Grounding (Table 6 style)

| Model | Win Basic | Win Adv | Mac Basic | Mac Adv | Linux Basic | Linux Adv | iOS Basic | iOS Adv | Android Basic | Android Adv | Web Basic | Web Adv | Avg |
|-------|-----------|---------|-----------|---------|-------------|-----------|-----------|---------|---------------|-------------|-----------|---------|-----|
| UI-TARS-72B-DPO | 78.60 | 51.84 | 80.29 | 62.72 | 68.59 | 51.53 | 90.76 | 81.21 | 92.98 | 80.00 | 88.06 | 68.51 | 74.25 |
| InternVL3-72B | 70.11 | 42.64 | 75.65 | 52.31 | 59.16 | 41.33 | 93.63 | 80.61 | 92.70 | 78.59 | 90.65 | 65.91 | 72.20 |
| UGround-V1-7B | 66.79 | 38.97 | 71.30 | 48.55 | 56.54 | 31.12 | 92.68 | 70.91 | 93.54 | 70.99 | 88.71 | 64.61 | 65.68 |
| UI-TARS-1.5-7B | 68.27 | 38.97 | 68.99 | 44.51 | 64.40 | 37.76 | 88.54 | 69.39 | 90.45 | 69.29 | 80.97 | 56.49 | 64.32 |
| Qwen-Max-VL | 43.91 | 36.76 | 58.84 | 56.07 | 53.93 | 30.10 | 77.39 | 59.09 | 79.49 | 70.14 | 74.84 | 58.77 | 58.03 |
| **GPT-5.5 (Ours)** | **94.03** | **83.46** | **91.86** | **86.73** | **89.01** | **78.57** | **97.45** | **92.73** | **97.47** | **94.37** | **97.09** | **87.91** | **91.52** |

## By Difficulty

| Level | Samples | Correct | Accuracy |
|-------|---------|---------|----------|
| Basic | 1787 | 1691 | **94.89%** |
| Advanced | 1807 | 1580 | **88.17%** |
| **Total** | **3594** | **3271** | **91.52%** |

## By Platform

| Platform | Samples | Correct | Accuracy |
|----------|---------|---------|----------|
| Android | 711 | 682 | 95.9% |
| iOS | 644 | 612 | 95.0% |
| Web | 618 | 569 | 92.5% |
| macOS | 691 | 610 | 89.3% |
| Windows | 543 | 474 | 88.8% |
| Linux | 387 | 324 | 83.7% |
| **Total** | **3594** | **3271** | **91.52%** |

> All 20 WF are `NoVerifiedTarget` — genuine hard cases the model cannot locate even after iterative zoom with retries. Not network errors.

## Files
- `results/gpt_5_5/full_report.md` — summary report
- `results/gpt_5_5/full_summary.json` — aggregated stats by platform
- `results/gpt_5_5/results.jsonl` — 3,594 per-sample records

## Run Info
- Run directory: `runs/gui_grounding/gui_grounding_mmbench_gui_l2_full_20260602_2040/`
