# OSWorld GIMP Domain - GPT-5.5 Run Errors

> 26 tasks | **50%** (5/10 evaluated) | 2026-05-17

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 26 |
| Evaluated | 10 |
| Pass (1.0) | 5 |
| Fail (0.0) | 5 |
| Not reached | 16 |
| Score so far | 50% (5/10) |

**Test environment:** Ubuntu VM at `172.16.105.130`, 1920x1080, `openai-codex/gpt-5.5` via GUI Agent Harness

**Repo state:** `b6cd6ea` when the run started; this document was later pushed in commit `44cf59f`.

**Run directory:** `runs/gimp_all_20260517_194037`

**Command pattern:**

```bash
.venv/bin/python benchmarks/osworld/run_osworld_task.py <task_index> \
  --domain gimp \
  --vm 172.16.105.130 \
  --max-steps 15 \
  --provider openai-codex \
  --model gpt-5.5
```

## Detailed Results

| # | Task ID | Instruction | Score | Steps | Time | Notes |
|---|---------|-------------|-------|-------|------|-------|
| 1 | 7a4deb26 | Tone down photo brightness | 0.0 FAIL | 8 | 175s | Runner said SUCCESS, evaluator missed `edited_darker.png`; model session errors |
| 2 | 554785e9 | Enhance color vibrancy | 1.0 PASS | 6 | 121s | Recovered from one `plan_next_action` model error |
| 3 | 77b8ab4d | Export photo to desktop as `export.jpg` | 1.0 PASS | 7 | 135s | No blocking error beyond missing proxy config warning |
| 4 | f4aec372 | Place yellow triangle at picture center | 0.0 FAIL | 15 | 198s | Drag target not found; screenshot read then failed repeatedly; output file missing |
| 5 | d52d6308 | Remove GIMP left dock | 1.0 PASS | 3 | 175s | No blocking error beyond missing proxy config warning |
| 6 | 2a729ded | Make image background transparent | 0.0 FAIL | 15 | 328s | HuggingFace download retries; `verify_step` model error; screenshot read cascade; output file missing |
| 7 | b148e375 | Add a new layer named `Square` | 1.0 PASS | 5 | 91s | Recovered from one `plan_next_action` model error |
| 8 | a746add2 | Open Vignette filter window | 1.0 PASS | 8 | 291s | Recovered from model errors in target lookup / verification |
| 9 | 7b7617bd | Set minimum undo steps to 100 | 0.0 FAIL | 15 | 205s | Multiple model errors; screenshot read cascade; evaluator failed to get GIMP config |
| 10 | d16c99dc | Resize dog layer height to 512 px | 0.0 FAIL | 15 | n/a | Download retries; model error; screenshot read cascade; evaluator missed `resized.png`; interrupted after score |
| 11-26 | - | Not reached | - | - | - | Batch stopped after task 10 |

## Error Details

| # | Primary failure | Secondary symptoms | Evaluator result | Log |
|---|-----------------|--------------------|------------------|-----|
| 1 | `verify_step()` and `conclusion()` returned `Agent session failed` | HuggingFace SSL EOF retry | Missing `/home/user/Desktop/edited_darker.png`; score 0.0 | `task_1.log` |
| 2 | `plan_next_action()` returned `Agent session failed` | Recovered on later steps | PASS; score 1.0 | `task_2.log` |
| 3 | No blocking error observed | Missing proxy config warning only | PASS; score 1.0 | `task_3.log` |
| 4 | Drag target failed: `End not found: center of the white canvas` | `/tmp/gui_agent_screen.png` read errors; `need at least one array to stack` on steps 3-15; `conclusion()` model error | Missing `/home/user/Desktop/Triangle_In_The_Middle.png`; score 0.0 | `task_4.log` |
| 5 | No blocking error observed | Missing proxy config warning only | PASS; score 1.0 | `task_5.log` |
| 6 | `verify_step()` returned `Agent session failed` | HuggingFace timeout / SSL EOF retries; screenshot read errors on steps 5-15; `conclusion()` model error | Missing `/home/user/Desktop/dog_without_background.png`; score 0.0 | `task_6.log` |
| 7 | `plan_next_action()` returned `Agent session failed` | Recovered on later steps | PASS; score 1.0 | `task_7.log` |
| 8 | `find_target_in_known()` and `verify_step()` returned `Agent session failed` | Recovered by coordinate fallback and later actions | PASS; score 1.0 | `task_8.log` |
| 9 | Multiple `plan_next_action()` / `verify_step()` model errors | Screenshot read errors on steps 13-15; `conclusion()` got HTTP 400 invalid image | Failed to get GIMP config; score 0.0 | `task_9.log` |
| 10 | `verify_step()` / `conclusion()` model path failed | HuggingFace SSL EOF retries; screenshot read errors on steps 8-15; `conclusion()` got HTTP 400 invalid image | Missing `/home/user/Desktop/resized.png`; score 0.0 | `task_10.log` |

## Error Categories

| Category | Affected tasks | Evidence | Notes |
|----------|----------------|----------|-------|
| Opaque model/session failure | 1, 2, 4, 6, 7, 8, 9, 10 | `RuntimeError: Agent session failed` | The detailed traceback/error-message fix does not appear active in the dependency path used by this run. |
| Invalid image passed to model | 9, 10 | OpenAI HTTP 400: image data is not a valid image | Usually appears after screenshot read failures. |
| Screenshot/read cascade | 4, 6, 9, 10 | `WARNING Image Read Error /tmp/gui_agent_screen.png`; `ValueError: need at least one array to stack` | Likely secondary after an earlier action/model failure. |
| Expected output missing | 1, 4, 6, 10 | Evaluator cannot retrieve expected desktop file | Could be execution failure, export failure, or filename/path mismatch. |
| HuggingFace asset download instability | 1, 6, 10 | SSL EOF, read timeout, curl fallback | Setup eventually recovered on 6 and 10, but with long delays. |
| Missing proxy config warning | 1-10 | `evaluation_examples/settings/proxy/dataimpulse.json` not found | Non-blocking for passing tasks 2, 3, 5, 7, 8. |

## Handoff Notes

- Confirm which OpenProgram / OpenAICodexRuntime revision is installed in `.venv`; the traceback-improvement commit does not appear active in these logs.
- Debug why a failed `verify_step()` or locate/drag failure leaves `/tmp/gui_agent_screen.png` unreadable and causes repeated `need at least one array to stack`.
- For failed export tasks 1, 4, 6, and 10, check whether the VM desktop contains a differently named output file after failure.
- Consider pre-caching HuggingFace OSWorld assets before full batch runs; setup download instability adds minutes and noise.
