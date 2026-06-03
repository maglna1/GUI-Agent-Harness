# Legacy Iter-Zoom Artifacts

This directory keeps small, Git-tracked historical scripts and notes that were
previously stored under `runs/screenspot_pro/`.

They are retained for auditability and reference only. Current reusable entry
points live one level up in `benchmarks/screenspot_pro/`:

- `start_full_autoretry.py`
- `start_screenspot_versions.py`
- `start_gui_grounding_datasets.py`
- `report_full_final.py`
- `report_screenspot_versions.py`
- `report_gui_grounding_datasets.py`

Large result files, caches, scratch work directories, and run outputs remain
local-only under `runs/`.
