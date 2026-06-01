"""ScreenSpot-Pro locator.

ScreenSpot-Pro is a static screenshot benchmark, not a live application. It
does not benefit from app memory, workflow learning, or unknown-component
labeling. Keep its control flow explicit:

1. verified crop refinement
2. active controller fallback
3. return None if no verified target is found

Environment variables in this module are tuning knobs only. They do not enable
or disable alternate locator pipelines.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

from gui_harness.planning import active_localization as active
from gui_harness.utils import parse_json
from gui_harness.error_monitor import reraise_if_fatal


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class ScreenSpotLocatorConfig:
    region_limit: int = 4
    active_rounds: int = 2
    active_top_k: int = 80
    snap_px: int = 80
    require_direct_snap: bool = True
    direct_crop_width: int = 360
    direct_crop_height: int = 240
    refine_crop_width: int = 360
    refine_crop_height: int = 260

    @classmethod
    def from_env(cls) -> "ScreenSpotLocatorConfig":
        return cls(
            region_limit=_env_int("GUI_HARNESS_SCREENSPOT_REGION_LIMIT", 4),
            active_rounds=_env_int("GUI_HARNESS_SCREENSPOT_ACTIVE_ROUNDS", 2),
            active_top_k=_env_int("GUI_HARNESS_SCREENSPOT_ACTIVE_TOPK", 80),
            snap_px=_env_int("GUI_HARNESS_SCREENSPOT_SNAP_PX", 80),
            require_direct_snap=_env_bool("GUI_HARNESS_SCREENSPOT_REQUIRE_DIRECT_SNAP", True),
            direct_crop_width=_env_int("GUI_HARNESS_SCREENSPOT_DIRECT_CROP_W", 360),
            direct_crop_height=_env_int("GUI_HARNESS_SCREENSPOT_DIRECT_CROP_H", 240),
            refine_crop_width=_env_int("GUI_HARNESS_SCREENSPOT_REFINE_CROP_W", 360),
            refine_crop_height=_env_int("GUI_HARNESS_SCREENSPOT_REFINE_CROP_H", 260),
        )


def screenspot_locate(
    task: str,
    target: str,
    img_path: str,
    img_w: int,
    img_h: int,
    candidates: list[dict],
    runtime,
    work_dir: Optional[str] = None,
    config: Optional[ScreenSpotLocatorConfig] = None,
) -> Optional[dict]:
    """Locate one ScreenSpot-Pro click target using a fixed benchmark flow."""
    if runtime is None:
        return None

    config = config or ScreenSpotLocatorConfig.from_env()
    out_dir = work_dir or os.environ.get("GUI_HARNESS_ACTIVE_LOC_DIR") or tempfile.gettempdir()
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    located = _candidate_first_select(task, target, img_path, candidates, runtime, out_dir, config)
    if located:
        return located

    located = _verified_crop_refine(task, target, img_path, img_w, img_h, runtime, out_dir, config, candidates)
    if located:
        return located

    return _active_controller_fallback(
        task=task,
        target=target,
        img_path=img_path,
        img_w=img_w,
        img_h=img_h,
        candidates=candidates,
        runtime=runtime,
        out_dir=out_dir,
        config=config,
    )


def _candidate_first_select(
    task: str,
    target: str,
    img_path: str,
    candidates: list[dict],
    runtime,
    out_dir: str,
    config: ScreenSpotLocatorConfig,
) -> Optional[dict]:
    """Prefer bounded OCR/component candidates before free-form localization."""
    pool = list(candidates)
    attempts = min(3, max(1, config.active_rounds + 1))
    for attempt in range(attempts):
        selected = active.rerank_candidates(task, target, img_path, pool, runtime)
        if not selected:
            return None
        selected["source"] = "screenspot_candidate_first"
        selected["grounding_type"] = "candidate_first_rerank"
        verifier = active.verify_candidate(task, target, img_path, selected, runtime, out_dir=out_dir)
        selected["pre_click_verifier"] = verifier
        verdict = str(verifier.get("is_target", "")).lower()
        print(
            f"  [screenspot_locate] candidate-first attempt {attempt + 1}: "
            f"{selected.get('name')} at ({selected.get('cx')},{selected.get('cy')}) "
            f"verdict={verdict} clicked={verifier.get('clicked_visible_element', '')!r} "
            f"target={verifier.get('target_visible_element', '')!r} "
            f"evidence={verifier.get('evidence', '')!r}",
            file=__import__("sys").stderr,
        )
        if verdict == "yes" and verifier.get("suggestion") != "zoom":
            return selected
        active._remove_rejected_candidate(pool, selected)
    return None


def _verified_crop_refine(
    task: str,
    target: str,
    img_path: str,
    img_w: int,
    img_h: int,
    runtime,
    out_dir: str,
    config: ScreenSpotLocatorConfig,
    candidates: list[dict],
) -> Optional[dict]:
    regions = active.propose_regions(
        task,
        target,
        img_path,
        img_w,
        img_h,
        runtime,
        max_regions=config.region_limit,
        candidates=candidates,
    )
    for region in regions:
        verifier = active.verify_region_crop(task, target, img_path, region, runtime, out_dir)
        verdict = str(verifier.get("contains_target", "")).lower()
        print(
            f"  [screenspot_locate] region {region.get('name')} {region.get('bbox')} "
            f"verdict={verdict} target={verifier.get('target_visible_element', '')!r} "
            f"evidence={verifier.get('evidence', '')!r}",
            file=__import__("sys").stderr,
        )
        if verdict != "yes" or verifier.get("suggestion") == "try_next":
            continue

        selected = active.refine_click_in_region(task, target, img_path, region, runtime, out_dir, candidates=candidates)
        if not selected:
            continue
        selected["crop_region_verifier"] = verifier

        final_verifier = active.verify_candidate(task, target, img_path, selected, runtime, out_dir=out_dir)
        selected["pre_click_verifier"] = final_verifier
        final_verdict = str(final_verifier.get("is_target", "")).lower()
        print(
            f"  [screenspot_locate] refined click ({selected.get('cx')},{selected.get('cy')}) "
            f"verdict={final_verdict} evidence={final_verifier.get('evidence', '')!r}",
            file=__import__("sys").stderr,
        )
        if final_verdict == "yes" and final_verifier.get("suggestion") != "zoom":
            return selected
    return None


def _active_controller_fallback(
    task: str,
    target: str,
    img_path: str,
    img_w: int,
    img_h: int,
    candidates: list[dict],
    runtime,
    out_dir: str,
    config: ScreenSpotLocatorConfig,
) -> Optional[dict]:
    pool = list(candidates)
    crop_paths: list[tuple[str, str]] = []
    rejected: list[str] = []

    for round_idx in range(config.active_rounds):
        has_crop_context = bool(crop_paths)
        context = f"""Task: {task}
Target: {target}
Screenshot size: {img_w}x{img_h}
Round: {round_idx + 1}/{config.active_rounds}

You are localizing one click target in a static screenshot. Use the full image,
OCR text boxes, detected component boxes, and any crop images from previous
rounds. Decide ONE action:
- click: choose a final click point or candidate_id when the target is visible.
  Prefer candidate_id whenever a candidate box matches. The click must be at
  the center of the target component/text box, not near an edge or merely close
  to the label.
- crop: request up to 3 regions to inspect more closely if the target is not
  clear enough in the full screenshot/candidates.
- fail: if there is not enough evidence.

Be conservative: if the proposed click might be a different UI element, choose
crop or fail instead of click.

Recent rejected candidates:
{chr(10).join(rejected[-4:]) or "(none)"}

Candidate UI elements:
{active._candidate_lines(pool, config.active_top_k)}

Reply with ONLY JSON:
{{
  "action": "click|crop|fail",
  "candidate_id": "c0 or empty",
  "x": 0,
  "y": 0,
  "regions": [
    {{"name": "short_name", "bbox": [x1, y1, x2, y2], "reasoning": "..."}}
  ],
  "confidence": 0.0,
  "reasoning": "..."
}}"""
        content = [{"type": "text", "text": context}, {"type": "image", "path": img_path}]
        for name, path in crop_paths[-3:]:
            content.append({"type": "text", "text": f"Crop image: {name}"})
            content.append({"type": "image", "path": path})

        reply = runtime.exec(content=content)
        try:
            decision = parse_json(reply)
        except Exception:
            rejected.append(f"round {round_idx + 1}: unparseable controller reply")
            continue

        action = str(decision.get("action", "")).lower().strip()
        if action == "click":
            selected = _selection_from_click_decision(decision, pool, img_w, img_h, has_crop_context, config)
            if selected is None:
                rejected.append(f"round {round_idx + 1}: invalid click decision")
                continue
            if selected.get("direct_unsnapped") and config.require_direct_snap and not has_crop_context:
                _add_direct_click_crop(img_path, selected, pool, crop_paths, out_dir, img_w, img_h, round_idx, config)
                rejected.append(
                    f"round {round_idx + 1}: rejected unsnapped direct pixel at "
                    f"({selected.get('cx')},{selected.get('cy')}); request crop or candidate_id"
                )
                continue

            selected["reasoning"] = decision.get("reasoning", "")
            verifier = active.verify_candidate(task, target, img_path, selected, runtime, out_dir=out_dir)
            selected["pre_click_verifier"] = verifier
            verdict = str(verifier.get("is_target", "")).lower()
            if verdict == "yes" and verifier.get("suggestion") != "zoom":
                if selected.get("direct_unsnapped"):
                    refined = _refine_direct_on_crop(task, target, img_path, selected, runtime, out_dir, img_w, img_h, config)
                    if refined:
                        refined_verifier = active.verify_candidate(task, target, img_path, refined, runtime, out_dir=out_dir)
                        refined["pre_click_verifier"] = refined_verifier
                        refined_verdict = str(refined_verifier.get("is_target", "")).lower()
                        if refined_verdict == "yes" and refined_verifier.get("suggestion") != "zoom":
                            return refined
                        print(
                            f"  [screenspot_locate] refined direct rejected at "
                            f"({refined.get('cx')},{refined.get('cy')}): "
                            f"verdict={refined_verdict} suggestion={refined_verifier.get('suggestion')} "
                            f"evidence={refined_verifier.get('evidence', '')!r}",
                            file=__import__("sys").stderr,
                        )
                return selected

            print(
                f"  [screenspot_locate] verifier rejected {selected.get('name')} "
                f"at ({selected.get('cx')},{selected.get('cy')}): "
                f"verdict={verdict} suggestion={verifier.get('suggestion')} "
                f"clicked={verifier.get('clicked_visible_element', '')!r} "
                f"target={verifier.get('target_visible_element', '')!r} "
                f"evidence={verifier.get('evidence', '')!r}",
                file=__import__("sys").stderr,
            )
            if verdict == "no":
                active._remove_rejected_candidate(pool, selected)
            rejected.append(
                f"round {round_idx + 1}: rejected {selected.get('name')} at "
                f"({selected.get('cx')},{selected.get('cy')}): {verifier.get('evidence', '')}"
            )
            continue

        if action == "crop":
            _append_requested_crops(decision, img_path, img_w, img_h, pool, crop_paths, out_dir, round_idx)
            continue

        rejected.append(f"round {round_idx + 1}: controller failed or declined: {decision.get('reasoning', '')}")

    return None


def _selection_from_click_decision(
    decision: dict,
    pool: list[dict],
    img_w: int,
    img_h: int,
    has_crop_context: bool,
    config: ScreenSpotLocatorConfig,
) -> Optional[dict]:
    selected = None
    candidate_id = str(decision.get("candidate_id", "")).strip()
    if candidate_id:
        selected = active._candidate_by_id(pool, candidate_id)
    if selected:
        selected = active._centered_location(selected)
        selected.update({
            "name": selected.get("label") or selected.get("id") or "active_loop_candidate",
            "source": "screenspot_active_loop",
            "grounding_type": "active_loop_candidate",
            "active_confidence": float(decision.get("confidence", 0) or 0),
        })
        return selected

    try:
        cx = int(round(float(decision.get("x", 0))))
        cy = int(round(float(decision.get("y", 0))))
    except (TypeError, ValueError):
        return None
    if cx <= 0 or cy <= 0 or cx > img_w or cy > img_h:
        return None

    direct = {
        "id": "direct",
        "label": "direct_pixel",
        "name": "direct_pixel",
        "source": "screenspot_active_loop",
        "grounding_type": "active_loop_direct_pixel",
        "cx": cx,
        "cy": cy,
        "x": cx - 24,
        "y": cy - 24,
        "w": 48,
        "h": 48,
        "confidence": decision.get("confidence", 0.0),
    }
    return _snap_direct_click_to_candidate(direct, pool, config)


def _snap_direct_click_to_candidate(selected: dict, candidates: list[dict], config: ScreenSpotLocatorConfig) -> dict:
    cx = int(selected.get("cx", 0) or 0)
    cy = int(selected.get("cy", 0) or 0)
    best: Optional[tuple[float, dict]] = None
    for cand in candidates:
        box = active._candidate_box(cand)
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        ccx = int(round((box[0] + box[2]) / 2))
        ccy = int(round((box[1] + box[3]) / 2))
        inside = box[0] <= cx <= box[2] and box[1] <= cy <= box[3]
        dist2 = float((ccx - cx) ** 2 + (ccy - cy) ** 2)
        if not inside and dist2 > config.snap_px ** 2:
            continue
        label = (cand.get("label") or cand.get("name") or "").strip()
        source = str(cand.get("source") or cand.get("type") or "")
        source_bonus = -10000.0 if source in {"ocr", "text"} or label else 0.0
        inside_bonus = -20000.0 if inside else 0.0
        score = dist2 + source_bonus + inside_bonus
        if best is None or score < best[0]:
            best = (score, cand)
    if best is None:
        result = dict(selected)
        result["direct_unsnapped"] = True
        result["snap_reason"] = "no nearby detected OCR/component candidate for direct click"
        return result

    snapped = active._centered_location(best[1])
    snapped.update({
        "id": snapped.get("id") or "direct_snapped",
        "name": snapped.get("label") or snapped.get("name") or "direct_snapped",
        "source": "screenspot_active_loop",
        "grounding_type": "active_loop_direct_snapped_to_candidate",
        "active_confidence": selected.get("confidence", selected.get("active_confidence", 0.0)),
        "original_direct_click": [cx, cy],
        "snap_reason": "direct click snapped to nearest detected component center before verification",
    })
    return snapped


def _append_requested_crops(
    decision: dict,
    img_path: str,
    img_w: int,
    img_h: int,
    pool: list[dict],
    crop_paths: list[tuple[str, str]],
    out_dir: str,
    round_idx: int,
) -> None:
    regions = []
    for item in decision.get("regions", [])[:3]:
        bbox = item.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4:
            regions.append({
                "name": item.get("name", f"round_{round_idx + 1}_region"),
                "bbox": active._clamp_box(bbox, img_w, img_h),
                "reasoning": item.get("reasoning", ""),
            })
    for region in regions:
        x1, y1, x2, y2 = region["bbox"]
        if x2 <= x1 or y2 <= y1:
            continue
        img = Image.open(img_path).convert("RGB")
        crop = img.crop((x1, y1, x2, y2))
        safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(region["name"]))[:60]
        crop_path = Path(out_dir) / f"screenspot_round{round_idx + 1}_{safe_name}.png"
        crop.save(crop_path)
        crop_paths.append((f"{region['name']} bbox={region['bbox']}", str(crop_path)))
        for cand in active._detect_region_candidates(img_path, region, out_dir):
            cand["id"] = f"c{len(pool)}"
            pool.append(cand)


def _add_direct_click_crop(
    img_path: str,
    selected: dict,
    pool: list[dict],
    crop_paths: list[tuple[str, str]],
    out_dir: str,
    img_w: int,
    img_h: int,
    round_idx: int,
    config: ScreenSpotLocatorConfig,
) -> None:
    cx = int(selected.get("cx", 0) or 0)
    cy = int(selected.get("cy", 0) or 0)
    half_w = config.direct_crop_width // 2
    half_h = config.direct_crop_height // 2
    bbox = active._clamp_box([cx - half_w, cy - half_h, cx + half_w, cy + half_h], img_w, img_h)
    region = {
        "name": f"rejected_direct_round{round_idx + 1}",
        "bbox": bbox,
        "reasoning": "inspection crop around rejected direct pixel",
    }
    x1, y1, x2, y2 = bbox
    img = Image.open(img_path).convert("RGB")
    crop = img.crop((x1, y1, x2, y2))
    crop_path = Path(out_dir) / f"screenspot_round{round_idx + 1}_rejected_direct.png"
    crop.save(crop_path)
    crop_paths.append((f"{region['name']} bbox={bbox}", str(crop_path)))
    for cand in active._detect_region_candidates(img_path, region, out_dir):
        cand["id"] = f"c{len(pool)}"
        pool.append(cand)


def _refine_direct_on_crop(
    task: str,
    target: str,
    img_path: str,
    selected: dict,
    runtime,
    out_dir: str,
    img_w: int,
    img_h: int,
    config: ScreenSpotLocatorConfig,
) -> Optional[dict]:
    cx = int(selected.get("cx", 0) or 0)
    cy = int(selected.get("cy", 0) or 0)
    half_w = config.refine_crop_width // 2
    half_h = config.refine_crop_height // 2
    x1, y1, x2, y2 = active._clamp_box([cx - half_w, cy - half_h, cx + half_w, cy + half_h], img_w, img_h)
    img = Image.open(img_path).convert("RGB")
    crop = img.crop((x1, y1, x2, y2))
    crop_path = Path(out_dir) / f"screenspot_refine_{os.getpid()}_{abs(hash((img_path, cx, cy)))}.png"
    crop.save(crop_path)
    context = f"""Task: {task}
Target: {target}
Original screenshot crop origin: ({x1}, {y1})
Initial proposed global click: ({cx}, {cy})

You are given a local crop around the proposed click. Choose the exact center
of the requested clickable target in ORIGINAL GLOBAL screenshot coordinates.
If the initial point is slightly above/below/left/right of the real target,
correct it. For split controls, choose the specific sub-control requested by
the target, not the neighboring label/status/toggle area.

Reply with ONLY JSON:
{{"x": 0, "y": 0, "target_visible_element": "...", "confidence": 0.0, "reasoning": "..."}}"""
    try:
        reply = runtime.exec(content=[
            {"type": "text", "text": context},
            {"type": "image", "path": str(crop_path)},
        ])
        parsed = parse_json(reply)
        rx = int(round(float(parsed.get("x", 0))))
        ry = int(round(float(parsed.get("y", 0))))
        confidence = float(parsed.get("confidence", 0) or 0)
    except Exception as exc:
        reraise_if_fatal(exc)  # auth/timeout/transport must reach the runner
        return None
    if rx <= 0 or ry <= 0 or rx > img_w or ry > img_h:
        return None
    if abs(rx - cx) > half_w or abs(ry - cy) > half_h:
        return None
    refined = dict(selected)
    refined.update({
        "cx": rx,
        "cy": ry,
        "x": rx - 24,
        "y": ry - 24,
        "w": 48,
        "h": 48,
        "name": selected.get("name", "direct_pixel") + "_refined",
        "grounding_type": "active_loop_direct_crop_refined",
        "direct_refinement": {
            "input_point": [cx, cy],
            "crop_path": str(crop_path),
            "crop_box": [x1, y1, x2, y2],
            "target_visible_element": parsed.get("target_visible_element", ""),
            "confidence": confidence,
            "reasoning": parsed.get("reasoning", ""),
        },
    })
    return refined
