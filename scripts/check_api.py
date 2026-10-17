#!/usr/bin/env python3
"""Validate Qloo API credentials and test live connectivity."""
import os
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import shutil
import subprocess
import json

def main():
    print("=" * 60)
    print(" CultureForge AI — API & Hackathon Readiness Check")
    print("=" * 60)

    # 1. Check Qloo CLI
    qloo_bin = shutil.which("qloo")
    if not qloo_bin:
        print("❌ Qloo CLI: NOT FOUND")
        print("   Run: npm install --global @qloo/qloo-harness")
        sys.exit(1)
    print(f"✅ Qloo CLI: Found at {qloo_bin}")

    # 2. Check QLOO_API_KEY
    api_key = os.getenv("QLOO_API_KEY")
    config_file = Path.home() / ".qloo" / "config"
    has_config = config_file.is_file() and ("api-key" in config_file.read_text(encoding="utf-8") if config_file.exists() else False)

    if api_key and api_key != "your_qloo_api_key_here":
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
        print(f"✅ Qloo API Key: Configured in environment / .env ({masked})")
    elif has_config:
        print(f"✅ Qloo API Key: Configured in ~/.qloo/config")
    else:
        print("⚠️  Qloo API Key: NOT YET CONFIGURED")
        print("   👉 When you receive your key, add it to .env:")
        print("      QLOO_API_KEY=your_key_here")
        print("   👉 Or configure via CLI:")
        print("      qloo config set api-key YOUR_KEY")
        print("-" * 60)
        print("ℹ️  CultureForge AI is currently operating in MOCK mode.")
        print("   The app and backend are 100% functional with mock data.")
        return

    # 3. Test Live Call to Qloo CLI
    print("\n🔄 Testing live connection with Qloo API...")
    try:
        proc = subprocess.run(
            [qloo_bin, "exec", "find_tags", "--input", '{"query":"coffee","limit":1}'],
            capture_output=True, text=True, timeout=15
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            print("✅ Qloo API Connection: SUCCESSFUL!")
            print(f"   Response summary: {json.dumps(data, indent=2)[:200]}...")
            print("\n🎉 Everything is LIVE and working!")
        else:
            print("❌ Qloo API returned an error:")
            print(f"   Return code: {proc.returncode}")
            try:
                err_data = json.loads(proc.stdout)
                print(f"   Details: {err_data.get('error', {}).get('recovery', proc.stdout)}")
            except Exception:
                print(f"   Error: {proc.stderr or proc.stdout}")
    except Exception as exc:
        print(f"❌ Failed to reach Qloo API: {exc}")

if __name__ == "__main__":
    main()
