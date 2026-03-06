#!/usr/bin/env python3
"""UI regression guard for file panel overlap in the main workspace layout."""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

STREAMLIT_STARTUP_TIMEOUT_SEC = 45.0
PAGE_READY_TIMEOUT_SEC = 30.0

METRICS_JS = """
()=>{const r=document.querySelector('div.st-key-workspace_layout');const h=r?r.querySelector(':scope>[data-testid=stLayoutWrapper]>[data-testid=stHorizontalBlock]'):null;const shell=document.querySelector('div.st-key-file_panel_shell');const title=document.querySelector('div.st-key-workspace_layout h1');return JSON.stringify({shell:shell?{x:shell.getBoundingClientRect().x,y:shell.getBoundingClientRect().y,width:shell.getBoundingClientRect().width,right:shell.getBoundingClientRect().right}:null,shellPosition:shell?getComputedStyle(shell).position:null,titleX:title?title.getBoundingClientRect().x:null,cols:h?Array.from(h.children).map((el,i)=>({i:i,x:el.getBoundingClientRect().x,y:el.getBoundingClientRect().y,width:el.getBoundingClientRect().width,right:el.getBoundingClientRect().right})):[],viewport:{width:window.innerWidth,height:window.innerHeight}});}
""".strip()


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run_cmd(args: list[str], *, timeout_sec: float = 120.0, check: bool = True) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_sec)
    output = (proc.stdout or "") + (proc.stderr or "")
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(args)}\n{output.strip()}"
        )
    return output


def _extract_result_block(raw_output: str) -> str:
    lines = raw_output.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "### Result":
            continue
        for candidate in lines[idx + 1 :]:
            stripped = candidate.strip()
            if stripped:
                return stripped
    raise RuntimeError(f"Playwright result block not found.\n{raw_output.strip()}")


def _parse_metrics(raw_output: str) -> dict[str, Any]:
    literal = _extract_result_block(raw_output)
    decoded: Any
    try:
        decoded = json.loads(literal)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Playwright returned invalid JSON literal: {literal}") from exc

    if isinstance(decoded, str):
        try:
            decoded = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Playwright returned invalid JSON payload: {decoded}") from exc

    if not isinstance(decoded, dict):
        raise RuntimeError(f"Unexpected metrics payload type: {type(decoded).__name__}")
    return decoded


def _wait_for_http(url: str, *, timeout_sec: float, app_proc: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if app_proc.poll() is not None:
            logs = app_proc.stdout.read() if app_proc.stdout else ""
            raise RuntimeError(f"Streamlit terminated early.\n{logs.strip()}")
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:  # nosec: B310
                if 200 <= int(response.status) < 500:
                    return
        except urllib.error.URLError:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Streamlit server did not become ready in {timeout_sec:.0f}s: {url}")


def _wait_for_metrics(
    npx: str, session_id: str, *, timeout_sec: float, width: int, height: int
) -> dict[str, Any]:
    _run_cmd([npx, "--yes", "@playwright/cli", f"-s={session_id}", "resize", str(width), str(height)])

    deadline = time.monotonic() + timeout_sec
    last_error = ""
    while time.monotonic() < deadline:
        try:
            output = _run_cmd(
                [npx, "--yes", "@playwright/cli", f"-s={session_id}", "eval", METRICS_JS],
                timeout_sec=30.0,
            )
            metrics = _parse_metrics(output)
            if metrics.get("shell") and len(metrics.get("cols", [])) >= 2:
                return metrics
        except Exception as exc:  # noqa: BLE001 - keep last probe reason
            last_error = str(exc)
        time.sleep(0.5)

    details = f"\nLast probe error:\n{last_error}" if last_error else ""
    raise RuntimeError(f"Page metrics did not become available in {timeout_sec:.0f}s.{details}")


def _validate_layout(metrics: dict[str, Any], *, tolerance_px: float) -> list[str]:
    errors: list[str] = []
    shell = metrics.get("shell")
    cols = metrics.get("cols", [])

    if metrics.get("shellPosition") != "fixed":
        errors.append(f"file panel is not fixed (position={metrics.get('shellPosition')!r}).")

    if not shell:
        errors.append("file panel shell is missing.")
        return errors

    if len(cols) < 2:
        errors.append(f"expected at least 2 workspace columns, found {len(cols)}.")
        return errors

    col0 = cols[0]
    col1 = cols[1]
    if abs(float(col0.get("y", 0.0)) - float(col1.get("y", 0.0))) > 2.0:
        errors.append("workspace columns are wrapping to a new line.")

    shell_right = float(shell.get("right", 0.0))
    content_left = float(col1.get("x", 0.0))
    if shell_right > (content_left - tolerance_px):
        errors.append(
            "file panel overlaps content column "
            f"(shell_right={shell_right:.2f}, content_left={content_left:.2f}, tolerance={tolerance_px:.2f})."
        )

    return errors


def _terminate_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5.0)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1280, help="Viewport width in pixels.")
    parser.add_argument("--height", type=int, default=720, help="Viewport height in pixels.")
    parser.add_argument(
        "--tolerance-px",
        type=float,
        default=2.0,
        help="Allowed overlap tolerance in pixels.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    npx = shutil.which("npx")
    if not npx:
        print("ERROR: npx is required for ui_layout_check but was not found in PATH.")
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    port = _free_tcp_port()
    url = f"http://127.0.0.1:{port}"
    session_id = f"layout-check-{int(time.time())}"

    app_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.address",
        "127.0.0.1",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    app_proc = subprocess.Popen(  # noqa: S603 - trusted local command
        app_cmd,
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_for_http(url, timeout_sec=STREAMLIT_STARTUP_TIMEOUT_SEC, app_proc=app_proc)
        _run_cmd([npx, "--yes", "@playwright/cli", f"-s={session_id}", "open", url], timeout_sec=90.0)
        metrics = _wait_for_metrics(
            npx,
            session_id,
            timeout_sec=PAGE_READY_TIMEOUT_SEC,
            width=args.width,
            height=args.height,
        )
        issues = _validate_layout(metrics, tolerance_px=args.tolerance_px)
        if issues:
            print("UI_LAYOUT_CHECK: FAIL")
            for issue in issues:
                print(f"- {issue}")
            print("Measured metrics:")
            print(json.dumps(metrics, indent=2))
            return 1

        print("UI_LAYOUT_CHECK: PASS")
        print(json.dumps(metrics, indent=2))
        return 0
    finally:
        try:
            _run_cmd(
                [npx, "--yes", "@playwright/cli", f"-s={session_id}", "close"],
                timeout_sec=30.0,
                check=False,
            )
        finally:
            _terminate_process(app_proc)


if __name__ == "__main__":
    raise SystemExit(main())

