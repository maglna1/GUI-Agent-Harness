#!/usr/bin/env python3
"""OSWorld-G (564) × GPT-5.5 × iterative-zoom (sspro_stack_zoom.yaml, control 惯例)。
串行,单进程,--skip-existing 续跑。输出 runs/osworld_g/results.jsonl。
refusal 类(gt=[-1,-1,-1,-1])管线照样出点击 → 必然算错(方法无拒绝能力,如实计)。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

DATA = HERE / "data_osworld_g"


def main() -> int:
    from gui_harness.openprogram_compat import create_runtime
    from gui_harness.planning.component_memory import detect_components
    from gui_harness.planning import active_localization, screenspot_locator
    from run_screenspot_pro import load_locator_config

    samples = json.loads((DATA / "annotations" / "osworld_g.json").read_text(encoding="utf-8"))
    out = REPO / "runs/osworld_g/results.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    work = REPO / "runs/osworld_g/work"
    work.mkdir(parents=True, exist_ok=True)

    done = set()
    if out.exists():
        for l in open(out, encoding="utf-8"):
            try:
                done.add(json.loads(l)["sample_id"])
            except Exception:
                pass
    cfg = load_locator_config(str(HERE / "configs" / "sspro_stack_zoom.yaml"))
    rt = create_runtime(provider="openai-codex", model="gpt-5.5")

    f = open(out, "a", encoding="utf-8")
    todo = [s for s in samples if s["id"] not in done]
    print(f"OSWorld-G: {len(todo)}/{len(samples)} 待跑", flush=True)
    for i, s in enumerate(todo):
        sid = s["id"]
        img = DATA / "raw_images" / s["raw_image_path"]
        gt = s["bbox"]
        t0 = time.time()
        rec = {"sample_id": sid, "instruction": s["instruction"], "gt_bbox": gt,
               "osworld_box_type": s.get("osworld_box_type"),
               "osworld_polygon": s.get("osworld_polygon"),
               "ui_type": s.get("ui_type")}
        # refusal 题:无有效目标,正确答案=拒绝点击。本方法(keep_best)永远输出点击,
        # 结果必然算错。跑完整管线只会徒劳耗尽 8 轮+recrop+重试(单题十几分钟),
        # 故直接短路记 wrong(评分等价,不浪费算力)。
        if s.get("osworld_box_type") == "refusal":
            rec["prediction_px"] = None
            rec["correctness"] = "wrong"
            rec["location"] = {"grounding_type": "refusal_not_supported"}
            rec["elapsed_s"] = 0.0
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            continue
        try:
            if not img.exists():
                raise FileNotFoundError(img.name)
            det = detect_components(str(img))
            cands = active_localization.build_candidates([], det["texts"], det["icons"])
            located = screenspot_locator.screenspot_locate(
                task=s["instruction"], target=s["instruction"], img_path=str(img),
                img_w=det["img_w"], img_h=det["img_h"], candidates=cands, runtime=rt,
                work_dir=str(work), config=cfg)
            if located:
                cx, cy = int(located["cx"]), int(located["cy"])
                rec["prediction_px"] = [cx, cy]
                rec["correctness"] = "correct" if (gt[0] <= cx <= gt[2] and gt[1] <= cy <= gt[3]) else "wrong"
                rec["location"] = {k: located.get(k) for k in ("name", "grounding_type", "reasoning")}
            else:
                rec["prediction_px"] = None
                rec["correctness"] = "wrong"
        except Exception as exc:
            from gui_harness.error_monitor import reraise_if_fatal
            reraise_if_fatal(exc)
            rec["error"] = {"type": exc.__class__.__name__, "message": str(exc)[:200]}
            rec["correctness"] = "wrong"
        rec["elapsed_s"] = round(time.time() - t0, 1)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(todo)}", flush=True)
    f.close()

    rows = [json.loads(l) for l in open(out, encoding="utf-8") if l.strip()]
    ok = sum(r["correctness"] == "correct" for r in rows)
    gnd = [r for r in rows if r.get("osworld_box_type") != "refusal"]
    gok = sum(r["correctness"] == "correct" for r in gnd)
    print(f"\nOSWorld-G 全量: {ok}/{len(rows)} = {ok/max(1,len(rows)):.1%}", flush=True)
    print(f"  可定位子集(非 refusal): {gok}/{len(gnd)} = {gok/max(1,len(gnd)):.1%}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
