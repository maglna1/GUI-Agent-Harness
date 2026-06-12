#!/usr/bin/env python3
"""切块直问定位器(tile locator)——独立于 iterative_zoom 的新方法。

把截图切成带重叠的原生分辨率小块,每块独立问模型"目标是否完整可见,
在则给坐标+置信度",全图汇总取最高置信。无逐步缩小过程,不存在裁丢。

用法(独立评测,不接管线):
  python tile_locator.py --samples <jsonl of sample_ids>|all --limit N
输出 runs/sspro_tile/results.jsonl,可与 zoom 臂同题对比。
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402

DATA = HERE / "data"
TILE = 1280          # 每块边长(原生像素,不缩放)
OVERLAP = 280        # 重叠量 > 最大元素尺寸,保证每个元素至少在一块里完整出现
CONF_MIN = 0.35      # 低于此置信的块答案丢弃


def tiles_for(w: int, h: int):
    """带重叠的网格切块;小图就一块。"""
    out = []
    step = TILE - OVERLAP
    xs = list(range(0, max(1, w - OVERLAP), step)) or [0]
    ys = list(range(0, max(1, h - OVERLAP), step)) or [0]
    for y in ys:
        for x in xs:
            x2, y2 = min(w, x + TILE), min(h, y + TILE)
            out.append((max(0, min(x, x2 - TILE)), max(0, min(y, y2 - TILE)), x2, y2))
    # 去重(右/下边缘的块可能重合)
    return sorted(set(out))


def overview_with_box(img: Image.Image, box, out_path: Path):
    """缩小全图 + 红框标出当前块位置(给模型全局上下文:这块属于哪个窗口)。"""
    from PIL import ImageDraw
    scale = min(1.0, 1280 / max(img.size))
    ov = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS) if scale < 1 else img.copy()
    d = ImageDraw.Draw(ov)
    d.rectangle([box[0] * scale, box[1] * scale, box[2] * scale, box[3] * scale],
                outline="#ff2222", width=4)
    ov.save(out_path)


def ask_tile(runtime, parse_json, instr: str, img: Image.Image, box, work: Path, sid: str, ti: int):
    crop = img.crop(box)
    p = work / f"{sid}_t{ti}.png"
    crop.save(p)
    ov_p = work / f"{sid}_t{ti}_ov.png"
    overview_with_box(img, box, ov_p)
    prompt = f"""Target UI element: {instr}

Image 1 is the FULL screenshot (downscaled) with a RED rectangle marking a
region. Image 2 is that region at native resolution.
Use image 1 to understand the overall layout — which application/window/panel
the red region belongs to — and image 2 to inspect details.

If the target element is clearly and FULLY visible in image 2 (and image 1
confirms it is in the right application/window context), reply with its exact
click coordinates in IMAGE 2's pixels and your confidence. If it is absent,
cut off at an edge, in the wrong window, or only a lookalike, reply found=false.

Reply ONLY JSON: {{"found": true|false, "x": 0, "y": 0, "confidence": 0.0, "element": "..."}}"""
    try:
        reply = runtime.exec(content=[{"type": "text", "text": prompt},
                                      {"type": "image", "path": str(ov_p)},
                                      {"type": "image", "path": str(p)}], timeout_s=120)
        r = parse_json(reply)
        if not r.get("found"):
            return None
        x, y = float(r.get("x", 0)), float(r.get("y", 0))
        conf = float(r.get("confidence", 0) or 0)
        if conf < CONF_MIN or not (0 <= x <= box[2] - box[0] and 0 <= y <= box[3] - box[1]):
            return None
        return {"px": [int(box[0] + x), int(box[1] + y)], "conf": conf,
                "element": str(r.get("element", ""))[:60], "tile": ti}
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="openai-codex")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--only-wrong", action="store_true",
                    help="只跑 zoom 臂答错的题(快速冒烟)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="runs/sspro_tile/results.jsonl")
    args = ap.parse_args()

    zoom = {}
    for p in glob.glob(str(REPO / "runs/sspro_stack/zoom/*.jsonl")):
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                zoom[r["sample_id"]] = r
            except Exception:
                continue
    todo = sorted(zoom)
    if args.only_wrong:
        todo = [k for k in todo if zoom[k].get("correctness") != "correct"]
    if args.limit:
        todo = todo[: args.limit]

    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work = out_path.parent / "tiles"
    work.mkdir(exist_ok=True)
    done = set()
    if out_path.exists():
        for line in open(out_path, encoding="utf-8"):
            try:
                done.add(json.loads(line)["sample_id"])
            except Exception:
                pass
    todo = [k for k in todo if k not in done]
    print(f"tile locator: {len(todo)} samples", flush=True)

    from gui_harness.openprogram_compat import create_runtime
    from gui_harness.utils import parse_json
    runtime = create_runtime(provider=args.provider, model=args.model)

    f = open(out_path, "a", encoding="utf-8")
    for i, sid in enumerate(todo):
        r = zoom[sid]
        img_p = DATA / "images" / f"{sid}.png"
        if not img_p.exists():
            continue
        t0 = time.time()
        img = Image.open(img_p).convert("RGB")
        hits = []
        for ti, box in enumerate(tiles_for(img.width, img.height)):
            h = ask_tile(runtime, parse_json, r["instruction"], img, box, work, sid, ti)
            if h:
                hits.append(h)
        best = max(hits, key=lambda h: h["conf"]) if hits else None
        gt = r["gt_bbox"]
        ok = bool(best) and gt[0] <= best["px"][0] <= gt[2] and gt[1] <= best["px"][1] <= gt[3]
        f.write(json.dumps({
            "sample_id": sid, "instruction": r["instruction"], "gt_bbox": gt,
            "prediction_px": best["px"] if best else None,
            "correctness": "correct" if ok else "wrong",
            "n_hits": len(hits), "best": best,
            "zoom_correct": r.get("correctness") == "correct",
            "elapsed_s": round(time.time() - t0, 1),
        }, ensure_ascii=False) + "\n")
        f.flush()
        print(f"  [{i+1}/{len(todo)}] {sid}: {'对' if ok else '错'} hits={len(hits)} ({time.time()-t0:.0f}s)", flush=True)
    f.close()

    rows = [json.loads(l) for l in open(out_path, encoding="utf-8")]
    ok = sum(r["correctness"] == "correct" for r in rows)
    print(f"\ntile: {ok}/{len(rows)} = {ok/max(1,len(rows)):.1%}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
