# Qwen2.5-VL-3B GUI-AIMA-Like Data Run

This directory is reserved for GUI Agent Harness evaluation results using
Qwen2.5-VL-3B-Instruct on the GUI-AIMA-style public grounding datasets:
GUIAct, AndroidControl, Wave-UI, UGround single-round 60k, and GTA1 no-web 60k.

The run uses the GUI Agent Harness grounding pipeline, then scores each predicted
point against the original dataset ground-truth bbox/point annotation.

## Expected Files

- `results.jsonl`: one JSON object per evaluated sample.
- `errors.jsonl`: failed samples, if any.
- `full_summary.json`: aggregate counts and accuracy.
- `full_report.md`: human-readable report.

Large intermediate crops, screenshots, and per-step traces should go under:

`/home/zichuanfu2/GUI-Attention-Harness/runs/qwen25vl3b_gui_aima_like/work/`

## JSONL Schema

Each row in `results.jsonl` should follow the existing ScreenSpot-style format:

```json
{
  "sample_id": "GUIAct_xxx",
  "dataset": "GUIAct",
  "annotation_file": "guiact_bbox.json",
  "image_path": "/absolute/path/to/image.png",
  "instruction": "click ...",
  "gt_bbox": [x1, y1, x2, y2],
  "prediction_px": [x, y],
  "prediction_norm": [0.5, 0.5],
  "correctness": "correct",
  "location": {
    "source": "gui_agent_harness",
    "grounding_type": "iterative_zoom_crop_refine",
    "reasoning": "...",
    "api_model": "Qwen2.5-VL-3B-Instruct"
  },
  "error": null,
  "elapsed_s": 0.0
}
```

`correctness` should be one of:

- `correct`: predicted point falls inside the ground-truth box.
- `wrong`: predicted point is outside the ground-truth box.
- `wrong_format`: no valid point was produced.
