#!/usr/bin/env python3
"""
Pre-learn GIMP UI components by walking the top-level menu tour.

Usage:
    python3 learn_gimp.py              # default VM 172.16.82.132
    python3 learn_gimp.py --vm 10.x.x.x
    python3 learn_gimp.py --keep-meta  # don't wipe existing meta.json first
"""
import argparse
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

VM_PORT = 5000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm", default="172.16.82.132")
    ap.add_argument("--keep-meta", action="store_true")
    args = ap.parse_args()

    vm_url = f"http://{args.vm}:{VM_PORT}"
    os.environ["NO_PROXY"] = f"{args.vm}/24"
    os.environ["no_proxy"] = f"{args.vm}/24"

    urllib.request.urlopen(f"{vm_url}/screenshot", timeout=10)
    print(f"VM {vm_url} reachable.")

    from gui_harness.adapters.vm_adapter import patch_for_vm
    patch_for_vm(vm_url)

    from gui_harness.action import input as _input
    from gui_harness.memory import app_memory
    from gui_harness.planning.learn import learn_app_components
    from openprogram.providers import create_runtime

    # Focus GIMP window, dismiss any open menu/dialog
    import json as _json
    def _exec(cmd):
        urllib.request.urlopen(
            urllib.request.Request(
                f"{vm_url}/execute",
                data=_json.dumps({"command": cmd, "shell": True}).encode(),
                headers={"Content-Type": "application/json"},
            ), timeout=15,
        )
    _exec("wmctrl -a GIMP || true")
    time.sleep(0.5)
    _input.key_press("Escape")
    _input.key_press("Escape")
    time.sleep(0.5)

    # Wipe stale meta (old schema uses `pages`, incompatible with new learn)
    if not args.keep_meta:
        app_dir = app_memory.get_app_dir("gimp")
        meta_path = app_dir / "meta.json"
        if meta_path.exists():
            meta_path.unlink()
            print(f"Removed {meta_path}")

    runtime = create_runtime(provider="claude-code", model="opus")

    t0 = time.time()
    result = learn_app_components(app_name="gimp", runtime=runtime, force=True)
    elapsed = time.time() - t0

    print(f"\n=== DONE in {elapsed:.1f}s ===")
    import json
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
