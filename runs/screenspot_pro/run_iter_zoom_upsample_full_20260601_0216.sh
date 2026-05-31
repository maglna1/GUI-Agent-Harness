#!/usr/bin/env bash
set -euo pipefail

cd "/Users/fzkuji/Documents/GUI Agent/GUI-Agent-Harness"
eval "$(/Users/fzkuji/miniforge3/bin/conda shell.bash hook)"
conda activate gui-agent

export GUI_HARNESS_SCREENSPOT_LOCATOR_MODE=iterative_zoom
export GUI_HARNESS_SCREENSPOT_ITERATIVE_ROUNDS=5
export GUI_HARNESS_SCREENSPOT_ITERATIVE_REVIEW_FINAL=1
export GUI_HARNESS_SCREENSPOT_ITERATIVE_VERIFY_FINAL=0
export GUI_HARNESS_SCREENSPOT_ITERATIVE_FALLBACK_TO_CROP=0
export GUI_HARNESS_SCREENSPOT_ITERATIVE_CROP_COMMIT_GATE=1
export GUI_HARNESS_SCREENSPOT_ITERATIVE_CROP_RETRIES=3
export GUI_HARNESS_SCREENSPOT_ITERATIVE_STAGED_CROP=1
export GUI_HARNESS_SCREENSPOT_ITERATIVE_STAGE1_MIN_AREA_PCT=20
export GUI_HARNESS_SCREENSPOT_ITERATIVE_STAGE2_MIN_AREA_PCT=8

# Upsample design: keep interpolation, make small/flat final crops visibly larger.
export GUI_HARNESS_SCREENSPOT_ITERATIVE_MAX_SIDE=2048
export GUI_HARNESS_SCREENSPOT_ITERATIVE_MAX_SCALE=5
export GUI_HARNESS_SCREENSPOT_ITERATIVE_MIN_SHORT_SIDE=512
export GUI_HARNESS_SCREENSPOT_ITERATIVE_FINAL_MAX_SIDE=4096
export GUI_HARNESS_SCREENSPOT_ITERATIVE_FINAL_MAX_SCALE=8
export GUI_HARNESS_SCREENSPOT_ITERATIVE_FINAL_MIN_SHORT_SIDE=640

run_id="iter_zoom_upsample_full_pure_20260601_0216"
out_dir="runs/screenspot_pro/${run_id}"
mkdir -p "$out_dir/work"
output="$out_dir/results.jsonl"
ann_dir="benchmarks/screenspot_pro/data/annotations"

for ann_path in "$ann_dir"/*.json; do
  annotation="$(basename "$ann_path")"
  count="$(python -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$ann_path")"
  echo "[upsample_full] annotation=$annotation count=$count indexes=all" >&2
  python benchmarks/screenspot_pro/run_screenspot_pro.py \
    --annotation "$annotation" \
    --indexes all \
    --output "$output" \
    --work-dir "$out_dir/work/${annotation%.json}" \
    --runtime-retries 4 \
    --retry-provider-errors 2 \
    --sample-timeout-s 900 \
    --download-timeout-s 60 \
    --download-retries 5 \
    --skip-existing
done

python runs/screenspot_pro/report_iter_zoom_progress.py --run-dir "$out_dir" --max-visuals 50
