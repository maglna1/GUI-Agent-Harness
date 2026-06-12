#!/usr/bin/env python3
"""离线模拟"候选锚定裁剪否决"(crop veto)。

规则(纯代码,无 LLM):提议的裁剪框若把【所有】词面相关(relevance>0)候选
全部排除在外(且原图中确实存在这类候选),则该裁剪应被否决。

对 SSPro 新 zoom 跑分(runs/sspro_stack/zoom)逐行回放裁剪历史:
  - 错题且属"裁丢目标":否决是否会在丢失轮触发?(触发=有机会救)
  - 触发时,被裁掉的相关候选里是否真有贴近 gt 的?(救援有效性)
  - 对题(266 行):否决会误触发多少次?(churn 风险)
零调用,检测结果按图缓存。
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from gui_harness.planning.component_memory import detect_components  # noqa: E402
from gui_harness.planning import active_localization as active  # noqa: E402

DATA = HERE / "data"


def load_rows():
    rows = {}
    for p in glob.glob(str(REPO / "runs/sspro_stack/zoom/*.jsonl")):
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                rows[r["sample_id"]] = r
            except Exception:
                continue
    return rows


_DET = {}


def candidates_for(img_path: str):
    if img_path not in _DET:
        det = detect_components(img_path)
        _DET[img_path] = active.build_candidates([], det["texts"], det["icons"])
    return _DET[img_path]


def center(c):
    b = active._candidate_box(c)
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def inside(pt, box):
    return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]


def veto_fires(instr, cands, crop_box) -> bool:
    """有相关候选存在,且全部在提议框之外 -> 否决。"""
    rel = [c for c in cands if active._candidate_relevance(instr, c) > 0]
    if not rel:
        return False
    return all(not inside(center(c), crop_box) for c in rel)


def main() -> int:
    rows = load_rows()
    img_of = {}
    for sid in rows:
        p = DATA / "images" / f"{sid}.png"
        if p.exists():
            img_of[sid] = str(p)

    rescue_candidates = 0   # 错题:否决在丢失轮(或更早)触发
    rescue_quality = 0      # 且被排除的相关候选中有贴近 gt 的(<=60px)
    lost_total = 0
    fp_rows = 0             # 对题:历史中任意一轮被误否决的行数
    fp_events = 0
    processed = 0

    for sid, r in sorted(rows.items()):
        img = img_of.get(sid)
        if not img:
            continue
        hist = ((r.get("location") or {}).get("iterative_zoom") or {}).get("history") or []
        commits = [h for h in hist if h.get("next_box")]
        if not commits:
            continue
        processed += 1
        instr = r["instruction"]
        cands = candidates_for(img)
        gt = r["gt_bbox"]
        gtc = ((gt[0] + gt[2]) / 2, (gt[1] + gt[3]) / 2)
        correct = r.get("correctness") == "correct"

        if correct:
            fired = sum(1 for h in commits if veto_fires(instr, cands, h["next_box"]))
            if fired:
                fp_rows += 1
                fp_events += fired
        else:
            # 找丢失轮
            lost_idx = None
            for i, h in enumerate(commits):
                nb = h["next_box"]
                if not inside(gtc, nb):
                    lost_idx = i
                    break
            if lost_idx is None:
                continue
            lost_total += 1
            if veto_fires(instr, cands, commits[lost_idx]["next_box"]):
                rescue_candidates += 1
                rel = [c for c in cands if active._candidate_relevance(instr, c) > 0]
                near_gt = any(
                    abs(center(c)[0] - gtc[0]) <= 60 and abs(center(c)[1] - gtc[1]) <= 60
                    for c in rel
                )
                rescue_quality += near_gt
        if processed % 50 == 0:
            print(f"  {processed}... lost={lost_total} veto救点={rescue_candidates} 误触发行={fp_rows}", flush=True)

    print(f"\n回放 {processed} 行:")
    print(f"裁丢目标的错题: {lost_total}")
    print(f"  否决会在丢失轮触发(可救): {rescue_candidates}")
    print(f"  且相关候选确实贴着 gt(救援有效): {rescue_quality}")
    print(f"对题中否决误触发: {fp_rows} 行 / {fp_events} 次(误触发→重选裁剪,非致命,但有 churn)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
