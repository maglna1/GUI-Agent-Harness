# OSWorld Thunderbird Domain - GPT-5.5 Run Errors

> 15 tasks | **0.0%** (0/1 officially scored so far) | started 2026-05-18

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 15 |
| Run so far | 2 |
| Officially scored | 1 |
| Pass (1.0) | 0 |
| Numeric fail (0.0) | 1 |
| Eval error / N/A | 1 |
| Not reached | 13 |
| Score so far | 0.0% (0/1) |

**Test environment:** Ubuntu VM at `172.16.105.130`, 1920x1080, `openai-codex/gpt-5.5` via GUI Agent Harness

**Run directory:** `runs/thunderbird_all_20260518_0442`

**Command pattern:**

```bash
.venv/bin/python benchmarks/osworld/run_osworld_task.py <task_index> \
  --domain thunderbird \
  --vm 172.16.105.130 \
  --max-steps 15 \
  --provider openai-codex \
  --model gpt-5.5
```

## Detailed Results

| # | Task ID | Instruction | Score | Steps | Time | Notes |
|---|---------|-------------|-------|-------|------|-------|
| 1 | dfac9ee8 | Remove account `anonym-x2024@outlook.com` | N/A EVAL_ERROR | 15 | 181s | Runner hit immediate model failure then screenshot-read cascade; evaluator setup failed uploading `firefox_decrypt.py` to read-only VM Desktop |
| 2 | 15c3b339 | Access Outlook account `anonym-x2024@outlook.com` | 0.0 FAIL | 15 | 131s | Same immediate model failure and screenshot-read cascade; evaluator accessibility tree did not find account |
| 3-15 | - | Not reached | - | - | - | Continue from task 3 |

## Error Details

| # | Primary failure | Secondary symptoms | Evaluator result | Log |
|---|-----------------|--------------------|------------------|-----|
| 1 | `plan_next_action()` returned `Agent session failed` on step 1 | Screenshot read cascade on steps 2-15; conclusion got HTTP 400 invalid image | Evaluator setup failed: upload to `/home/user/Desktop/firefox_decrypt.py` returned read-only filesystem; score N/A | `task_1.log` |
| 2 | `plan_next_action()` returned `Agent session failed` on step 1 | Screenshot read cascade on steps 2-15; conclusion had one `Agent session failed` and one HTTP 400 invalid image | Evaluator checked accessibility tree and did not find `anonym-x2024@outlook.com`; score 0.0 | `task_2.log` |

## Error Categories

| Category | Affected tasks | Evidence | Notes |
|----------|----------------|----------|-------|
| Opaque model/session failure | 1, 2 | `RuntimeError: Agent session failed` | Triggered immediate execution collapse. |
| Screenshot/read cascade | 1, 2 | `WARNING Image Read Error /tmp/gui_agent_screen.png`; `ValueError: need at least one array to stack` | Started after the first model failure. |
| Invalid image passed to model | 1, 2 | OpenAI HTTP 400: image data is not a valid image | Appeared during conclusion after screenshot read failures. |
| Evaluator setup failure | 1 | Upload failed with status 500: read-only filesystem at `/home/user/Desktop/firefox_decrypt.py` | Separate from runner failure; official score is N/A. |
| HuggingFace asset download instability | 1 | SSL EOF retry while downloading `firefox_decrypt.py` | Download recovered; upload failed afterward. |
| Missing proxy config warning | 1, 2 | `evaluation_examples/settings/proxy/dataimpulse.json` not found | Non-blocking so far. |

## Handoff Notes

- Continue at Thunderbird task 3 in `runs/thunderbird_all_20260518_0442`.
- Official `test_all.json` lists 15 Thunderbird tasks; the older `benchmarks/osworld/thunderbird.md` says 24 and is stale.
- Treat official evaluator score as benchmark truth. Task 1 has no score because evaluator setup failed after runner failure.
- Watch for VM filesystem state. Task 1 evaluator could not upload to `/home/user/Desktop/firefox_decrypt.py` due to a read-only filesystem.
