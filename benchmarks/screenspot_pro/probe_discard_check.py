#!/usr/bin/env python3
"""离线验证"弃区检查"(用户提案):裁剪提交前,把被丢弃的区域单独亮出来
问模型"目标是否在被丢弃的部分里"。

回放 SSPro zoom 结果:
  - 17 个"裁丢目标"错题:在丢失轮渲染 A(保留区)/B(当前视野涂黑保留区,
    只露弃区),问"目标在 B 里吗"。理想答案=是(拦截成功)。
  - 30 个裁对的对照:同样渲染同样问。理想答案=否(不误拦)。
输出拦截率/误拦率。
"""
from __future__ import annotations

import glob
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from PIL import Image, ImageDraw  # noqa: E402

DATA = HERE / "data"


def load_zoom():
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


def commits(r):
    hist = ((r.get("location") or {}).get("iterative_zoom") or {}).get("history") or []
    return [h for h in hist if h.get("next_box")]


def lost_round(r):
    gt = r["gt_bbox"]
    cx, cy = (gt[0] + gt[2]) / 2, (gt[1] + gt[3]) / 2
    for i, h in enumerate(commits(r)):
        nb = h["next_box"]
        if not (nb[0] <= cx <= nb[2] and nb[1] <= cy <= nb[3]):
            return i
    return None


def render_pair(img, cur_box, next_box, work, tag):
    """A=保留区原生裁剪;B=当前视野,保留区涂黑(只看得见即将丢弃的部分)。"""
    a = img.crop(next_box)
    pa = work / f"{tag}_keep.png"
    a.save(pa)
    b = img.crop(cur_box).copy()
    d = ImageDraw.Draw(b)
    d.rectangle([next_box[0] - cur_box[0], next_box[1] - cur_box[1],
                 next_box[2] - cur_box[0], next_box[3] - cur_box[1]], fill="black")
    # 缩到合理尺寸
    if max(b.size) > 1400:
        s = 1400 / max(b.size)
        b = b.resize((int(b.width * s), int(b.height * s)), Image.LANCZOS)
    pb = work / f"{tag}_discard.png"
    b.save(pb)
    return pa, pb


def main() -> int:
    rows = load_zoom()
    lost, control = [], []
    for sid, r in sorted(rows.items()):
        img_p = DATA / "images" / f"{sid}.png"
        if not img_p.exists() or not commits(r):
            continue
        if r.get("correctness") != "correct":
            li = lost_round(r)
            if li is not None:
                lost.append((sid, r, li))
        else:
            control.append((sid, r))
    random.Random(7).shuffle(control)
    control = control[:30]
    print(f"裁丢案例 {len(lost)},对照 {len(control)}", flush=True)

    from gui_harness.openprogram_compat import create_runtime
    from gui_harness.utils import parse_json
    rt = create_runtime(provider="openai-codex", model="gpt-5.5")
    work = REPO / "runs/discard_probe"
    work.mkdir(parents=True, exist_ok=True)

    def probe(sid, r, idx):
        img = Image.open(DATA / "images" / f"{sid}.png").convert("RGB")
        cs = commits(r)
        h = cs[idx]
        cur_box = h["crop_box"] if isinstance(h.get("crop_box"), list) else [0, 0, img.width, img.height]
        pa, pb = render_pair(img, cur_box, h["next_box"], work, sid)
        prompt = f"""Target UI element: {r['instruction']}

We are about to zoom into a region of a screenshot. Image 1 is the region we
will KEEP. Image 2 shows the surrounding area we are about to DISCARD (the
kept region is blacked out).

Question: is the target element visible in image 2 (the part being discarded)?
Look carefully — answer yes only if you can actually see it there.

Reply ONLY JSON: {{"in_discarded": true|false, "confidence": 0.0, "where": "..."}}"""
        try:
            reply = rt.exec(content=[{"type": "text", "text": prompt},
                                     {"type": "image", "path": str(pa)},
                                     {"type": "image", "path": str(pb)}], timeout_s=120)
            p = parse_json(reply)
            return bool(p.get("in_discarded")), float(p.get("confidence", 0) or 0)
        except Exception as e:
            return None, str(e)

    catch = miss = 0
    for sid, r, li in lost:
        ans, conf = probe(sid, r, li)
        ok = ans is True
        catch += ok
        miss += ans is False
        print(f"  LOST {sid}: 拦截={'是' if ok else '否'} conf={conf}", flush=True)
    fa = ok_n = 0
    for sid, r in control:
        # 对照:检查它的第 1 个 commit(目标确实在保留区里)
        ans, conf = probe(sid, r, 0)
        if ans is None:
            continue
        ok_n += 1
        fa += ans is True
        print(f"  CTRL {sid}: 误报={'是' if ans else '否'}", flush=True)

    print(f"\n拦截成功 {catch}/{len(lost)};漏拦 {miss};对照误报 {fa}/{ok_n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
