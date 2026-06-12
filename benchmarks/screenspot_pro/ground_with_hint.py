#!/usr/bin/env python3
"""带外部知识提示的单题重定位:验证"搜索补知识"能否救回认不出的目标。

用法:
  python ground_with_hint.py <sample_id> "<从网上搜到的按钮位置/外观描述>"
对该题跑一次缩放定位(注入提示),打印 CORRECT/WRONG 与坐标。
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

DATA = HERE / "data"


def main() -> int:
    sid, hint = sys.argv[1], sys.argv[2]
    row = None
    for p in glob.glob(str(REPO / "runs/sspro_stack/zoom/*.jsonl")):
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("sample_id") == sid:
                row = r
                break
    if row is None:
        print("SAMPLE_NOT_FOUND")
        return 1
    img_p = DATA / "images" / f"{sid}.png"
    if not img_p.exists():
        print("IMAGE_NOT_FOUND")
        return 1

    instr = row["instruction"]
    # 注入提示:目标描述 = 原指令 + 文档线索
    target = f"{instr}. Documentation hint about this control: {hint}"

    from gui_harness.openprogram_compat import create_runtime
    from gui_harness.planning.component_memory import detect_components
    from gui_harness.planning import active_localization, screenspot_locator

    rt = create_runtime(provider="openai-codex", model="gpt-5.5")
    det = detect_components(str(img_p))
    cands = active_localization.build_candidates([], det["texts"], det["icons"])
    from run_screenspot_pro import load_locator_config
    cfg = load_locator_config(str(HERE / "configs" / "sspro_stack_zoom.yaml"))
    located = screenspot_locator.screenspot_locate(
        task=instr, target=target, img_path=str(img_p),
        img_w=det["img_w"], img_h=det["img_h"],
        candidates=cands, runtime=rt,
        work_dir=str(REPO / "runs/hint_probe/work"), config=cfg,
    )
    if not located:
        print("WRONG no_point")
        return 0
    gt = row["gt_bbox"]
    cx, cy = located["cx"], located["cy"]
    ok = gt[0] <= cx <= gt[2] and gt[1] <= cy <= gt[3]
    print(f"{'CORRECT' if ok else 'WRONG'} point=({cx},{cy}) gt={gt}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    raise SystemExit(main())
