#!/usr/bin/env python3
"""Validate Qloo credentials and configuration without burning API quota.

By default this script is READ-ONLY: it reports what is configured and what
the quota guard currently allows, and makes no network calls. Pass --live to
opt into a single test request.

Usage:
    python3 scripts/check_api.py            # read-only diagnostics
    python3 scripts/check_api.py --live     # also make one test request
    python3 scripts/check_api.py --live --operation recommend
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
HACKATHON_BASE_URL = "https://hackathon.api.qloo.com"


def load_qloo_config() -> dict:
    """Parse the CLI's private config (~/.qloo/config) without echoing secrets."""
    config_path = Path.home() / ".qloo" / "config"
    values = {}
    if not config_path.is_file():
        return values
    try:
        for line in config_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    except OSError:
        pass
    return values


def mask(value: str) -> str:
    return f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"


def read_budget_log() -> list[float]:
    path = Path(os.getenv('CULTUREFORGE_CACHE_DIR', Path.home() / '.cache' / 'cultureforge')) / 'qloo_calls.json'
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [float(s) for s in data.get("calls", []) if isinstance(s, (int, float))]
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="make one real API request")
    parser.add_argument("--operation", default="find_tags", help="workflow to test with --live")
    parser.add_argument("--input", default='{"query":"coffee","limit":1}', help="JSON input for --live")
    args = parser.parse_args()

    print("=" * 62)
    print(" CultureForge AI — Qloo readiness check")
    print("=" * 62)

    ok = True

    # 1. Harness availability
    qloo_bin = shutil.which("qloo")
    wrapper = ROOT / "scripts" / "qloo_exec.mjs"
    node_bin = shutil.which("node")
    if qloo_bin:
        print(f"[ok]   qloo CLI: {qloo_bin}")
    else:
        print("[warn] qloo CLI not found (only needed for interactive qloo commands)")
    if wrapper.is_file() and node_bin:
        print(f"[ok]   timeout-aware wrapper: {wrapper}")
    else:
        print("[warn] scripts/qloo_exec.mjs or node not available — live requests may time out")

    # 2. Credential
    config = load_qloo_config()
    env_key = os.getenv("QLOO_API_KEY", "").strip()
    file_key = config.get("api_key", "").strip()
    if env_key and env_key != "your_qloo_api_key_here":
        print(f"[ok]   API key: environment/.env ({mask(env_key)})")
    elif file_key:
        print(f"[ok]   API key: {Path.home() / '.qloo' / 'config'} ({mask(file_key)})")
    else:
        print("[warn] API key: NOT CONFIGURED")
        print("       qloo config set api-key YOUR_KEY   (or set QLOO_API_KEY in .env)")
        ok = False

    # 3. Base URL — the single most common cause of 401s
    base_url = os.getenv("QLOO_BASE_URL", "").strip() or config.get("base_url", "").strip()
    if not base_url:
        print("[warn] base URL: not set — the CLI would target https://api.qloo.com")
        print(f"       qloo config set base-url {HACKATHON_BASE_URL}")
        ok = False
    elif base_url.rstrip("/") == HACKATHON_BASE_URL:
        print(f"[ok]   base URL: {base_url} (hackathon endpoint)")
    else:
        print(f"[warn] base URL: {base_url}")
        print(f"       hackathon keys only work against {HACKATHON_BASE_URL} — expect 401")
        ok = False
    if config.get("trusted_base_url"):
        print("[ok]   base URL is trusted by the CLI")

    # 4. Quota guard state
    sys.path.insert(0, str(ROOT))
    from backend import config as run_config
    hour_limit = run_config.limit("QLOO_MAX_CALLS_PER_HOUR")
    day_limit = run_config.limit("QLOO_MAX_CALLS_PER_DAY")
    calls = read_budget_log()
    now = time.time()
    in_hour = sum(1 for stamp in calls if now - stamp < 3600)
    in_day = sum(1 for stamp in calls if now - stamp < 86400)
    print(f"[ok]   run profile: {run_config.run_profile()}"
          f"{'' if run_config.qloo_live_enabled() else ' (QLOO_LIVE_ENABLED=false: held evidence only)'}")
    print(f"[ok]   quota guard: {in_hour}/{run_config.describe_limit(hour_limit)} this hour, "
          f"{in_day}/{run_config.describe_limit(day_limit)} today")
    if ((hour_limit is not None and in_hour >= hour_limit)
            or (day_limit is not None and in_day >= day_limit)):
        print("[warn] quota guard is exhausted — live signals are paused")
        ok = False

    print("-" * 62)

    # 5. Optional live probe
    if not args.live:
        print("Read-only run: no API calls made. Use --live to send one test request.")
        return 0 if ok else 1

    if not (env_key or file_key):
        print("Cannot run --live without a credential.")
        return 1

    command = [node_bin, str(wrapper)] if (wrapper.is_file() and node_bin) else [qloo_bin]
    if not command[0]:
        print("Cannot run --live: no qloo CLI and no node wrapper.")
        return 1
    command += ["exec", args.operation, "--input", args.input]
    print(f"Live probe -> {args.operation} (this consumes quota)")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("[warn] live probe timed out after 120s")
        return 1
    if proc.returncode == 0:
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print("[warn] live probe returned unreadable output")
            return 1
        status = data.get("status") or ("error" if data.get("error") else "ok")
        count = data.get("result_count", len(data.get("results", []) or []))
        print(f"[ok]   live probe succeeded (status={status}, results={count})")
        return 0
    print("[warn] live probe failed:")
    try:
        detail = json.loads(proc.stdout).get("error", {})
        print(f"       code={detail.get('code')} recovery={detail.get('recovery')}")
    except (json.JSONDecodeError, AttributeError):
        print(f"       {proc.stderr.strip()[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
