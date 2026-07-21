#!/usr/bin/env python3
"""observe.py — automix-light's only script (observability only, stdlib only).

When a task finishes, /aml:go calls:
  observe.py task-done --since <ISO8601> --label "<task>" \
      [--feature "<feature name>"] [--note "<verification result>"] [--dry-run]
→ Sums per-model token usage over the window (since→now) from the session
  transcript (~/.claude/projects/<encoded cwd>/*.jsonl) and prints one
  "metrics: …" line to stdout for progress.md.
→ If langfuse in .aml/config.yaml is "on", also sends the same data to Langfuse
  (credentials are env-only).

Invariant: fully fail-open — any runtime failure prints one warning then exits 0.
Observability must never block implementation. (Only argparse usage errors exit 2.)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USAGE_FIELDS = ("input_tokens", "output_tokens",
                "cache_creation_input_tokens", "cache_read_input_tokens")

DEFAULT_HOST = "https://cloud.langfuse.com"

# Per-model-family pricing (USD/MTok, input/output) — same table as am pricing.py.
PRICING = {"opus": (5.0, 25.0), "fable": (10.0, 50.0),
           "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}
CACHE_WRITE_MULT = 1.25   # cache write ≈ 1.25× input price
CACHE_READ_MULT = 0.10    # cache read ≈ 0.1× input price


# ── time / formatting utils ──────────────────────────────────────────────────────────

def parse_ts(ts) -> datetime | None:
    if not ts:
        return None
    s = str(ts).strip().replace("Z", "+00:00")
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)   # BSD date's +1000 → +10:00
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return (dt.astimezone(timezone.utc)
            .isoformat(timespec="milliseconds").replace("+00:00", "Z"))


def humanize(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 10_000:
        return f"{round(n / 1000)}k"
    if n >= 1_000:
        return f"{n / 1000:.1f}k"
    return str(n)


def humanize_dur(secs: int) -> str:
    if secs >= 3600:
        return f"{secs // 3600}h {secs % 3600 // 60}m"
    if secs >= 60:
        return f"{secs // 60}m {secs % 60}s"
    return f"{secs}s"


# ── transcript discovery + aggregation (trimmed port of am task-metrics.py) ───────────────────

def projects_root() -> Path:
    return Path(os.environ.get("AML_CLAUDE_PROJECTS_DIR")
                or os.path.expanduser("~/.claude/projects"))


def _dir_cwd(d: Path) -> str | None:
    """The realpath cwd recorded in this transcript dir (None if absent)."""
    for f in sorted(d.glob("*.jsonl")):
        try:
            with f.open(encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    if i > 20:
                        break
                    if '"cwd"' not in line:
                        continue
                    try:
                        c = json.loads(line).get("cwd")
                    except Exception:
                        continue
                    if c:
                        return os.path.realpath(c)
        except OSError:
            continue
    return None


def transcript_dir() -> Path | None:
    """Transcript dir for the current cwd. The encoding (`[^A-Za-z0-9] → -`) is
    lossy, so verify against the recorded cwd; on mismatch/miss, scan all dirs."""
    root = projects_root()
    if not root.is_dir():
        return None
    cwd = os.path.realpath(os.getcwd())
    enc = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    cand = root / enc
    if cand.is_dir():
        dc = _dir_cwd(cand)
        if dc is None or dc == cwd:
            return cand
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d == cand:
            continue
        if _dir_cwd(d) == cwd:
            return d
    return None


def sum_by_model(start: datetime, end: datetime) -> dict[str, dict] | None:
    """Sum assistant usage within the window [start, end] per model.
    Transcript not found → None (measure line renders as 'metrics: unavailable')."""
    d = transcript_dir()
    if d is None:
        return None
    per: dict[str, dict] = {}
    start_epoch = start.timestamp()
    for f in d.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < start_epoch - 2:   # prune files that ended before the window
                continue
            fh = f.open(encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "assistant":
                    continue
                ts = parse_ts(rec.get("timestamp"))
                if ts is not None and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts is None or ts < start or ts > end:
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage") or {}
                model = msg.get("model") or "?"   # records with no model go to the "?" bucket (cost skipped)
                tot = per.setdefault(model, {k: 0 for k in USAGE_FIELDS})
                for k in USAGE_FIELDS:
                    tot[k] += usage.get(k, 0) or 0
    return per


# ── cost ────────────────────────────────────────────────────────────────────

def cost_usd(model: str, tok: dict) -> float | None:
    m = model.strip().lower()
    price = next((p for key, p in PRICING.items() if key == m or key in m), None)
    if price is None:
        return None
    inp, out = price
    return (tok["input_tokens"] / 1e6 * inp
            + tok["output_tokens"] / 1e6 * out
            + tok["cache_creation_input_tokens"] / 1e6 * inp * CACHE_WRITE_MULT
            + tok["cache_read_input_tokens"] / 1e6 * inp * CACHE_READ_MULT)


def fmt_usd(c: float) -> str:
    return f"${c:.4f}" if c < 0.01 else f"${c:.2f}"


# ── measure line rendering ──────────────────────────────────────────────────────────

def measure_line(dur_secs: int, per: dict[str, dict] | None) -> str:
    if per is None:
        return "metrics: unavailable (no session record found)"
    if not per:
        return f"metrics: {humanize_dur(dur_secs)} · no token record"
    items = sorted(per.items())
    costs = [cost_usd(m, t) for m, t in items]
    known = [c for c in costs if c is not None]
    total = sum(known) if known else None
    if len(items) == 1:
        m, t = items[0]
        line = (f"metrics: {m} · {humanize_dur(dur_secs)}"
                f" · tokens {humanize(t['input_tokens'])} in / {humanize(t['output_tokens'])} out"
                f" (cache {humanize(t['cache_read_input_tokens'])} r"
                f" / {humanize(t['cache_creation_input_tokens'])} w)")
    else:
        parts = [f"{m}({humanize(t['input_tokens'])} in/{humanize(t['output_tokens'])} out)"
                 for m, t in items]
        line = f"metrics: {humanize_dur(dur_secs)} · " + " + ".join(parts)
    if total is not None:
        line += f" · est. cost {fmt_usd(total)}"
    return line


# ── Langfuse (opt-in, default off — .aml/config.yaml absent = off) ───────────────

def config_get(key: str) -> str | None:
    """Read a key from .aml/config.yaml by first match (am get_config convention).
    The file is documented as two flat keys (langfuse/langfuse_host); even with
    nesting/duplicates, the first textual match in the file wins."""
    p = Path(".aml/config.yaml")
    if not p.is_file():
        return None
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(rf'\s*{key}:\s*["\']?([^"\'#\n]*)', line)
            if m:
                return m.group(1).strip() or None
    except (OSError, UnicodeDecodeError):
        return None
    return None


def langfuse_on() -> bool:
    return (config_get("langfuse") or "off").lower() == "on"


def resolve_creds() -> tuple[str | None, str | None, str]:
    public = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret = os.environ.get("LANGFUSE_SECRET_KEY")
    host = (os.environ.get("LANGFUSE_HOST") or config_get("langfuse_host")
            or DEFAULT_HOST).rstrip("/")
    return public, secret, host


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "task"


def build_batch(label: str, feature: str | None, note: str | None,
                since: datetime, end: datetime, dur_secs: int,
                per: dict[str, dict] | None) -> list[dict]:
    """One task → Langfuse ingestion batch. ids are deterministic from label+since."""
    tid = f"aml-{slug(label)}-{re.sub(r'[^0-9]', '', iso(since))[:14]}"
    items = sorted((per or {}).items())
    summary: dict = {"duration_sec": dur_secs, "models": dict(items)}
    known = [c for c in (cost_usd(m, t) for m, t in items) if c is not None]
    if known:
        summary["est_cost_usd"] = round(sum(known), 4)
    if note:
        summary["verify"] = note
    batch: list[dict] = []

    def envelope(etype: str, body: dict) -> None:
        batch.append({"id": f"{body['id']}-{etype}", "type": etype,
                      "timestamp": iso(end), "body": body})

    envelope("trace-create", {
        "id": tid, "name": f"aml:{label}",
        "sessionId": feature or Path.cwd().name,
        "timestamp": iso(since), "tags": ["aml"],
        "metadata": {"label": label, "cwd": Path.cwd().name},
        "input": label, "output": summary})
    for i, (m, t) in enumerate(items):
        envelope("generation-create", {
            "id": f"{tid}-gen{i}", "traceId": tid, "name": "task",
            "startTime": iso(since), "endTime": iso(end), "model": m,
            "usageDetails": {
                "input": t["input_tokens"], "output": t["output_tokens"],
                "cache_creation_input_tokens": t["cache_creation_input_tokens"],
                "cache_read_input_tokens": t["cache_read_input_tokens"]},
            "output": summary})
    if note:
        envelope("event-create", {
            "id": f"{tid}-verify", "traceId": tid, "name": "verify",
            "startTime": iso(end), "metadata": {"note": note}})
    return batch


def post(host: str, public: str, secret: str, batch: list[dict]) -> int | None:
    data = json.dumps({"batch": batch}).encode("utf-8")
    auth = base64.b64encode(f"{public}:{secret}".encode()).decode()
    req = urllib.request.Request(
        f"{host}/api/public/ingestion", data=data, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except Exception as exc:  # noqa: BLE001 — best-effort
        print(f"langfuse: send failed ({exc}) — continuing", file=sys.stderr)
        return None


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_task_done(args) -> None:
    since = parse_ts(args.since)
    if since is None:
        print("metrics: unavailable (could not read --since time)")
        return
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    end = now_utc()
    dur = max(0, int((end - since).total_seconds()))
    per = sum_by_model(since, end)
    print(measure_line(dur, per))
    if not langfuse_on():
        return
    batch = build_batch(args.label, args.feature, args.note, since, end, dur, per)
    if args.dry_run:
        print(json.dumps({"batch": batch}, ensure_ascii=False))
        return
    public, secret, host = resolve_creds()
    if not public or not secret:
        print("langfuse: on but LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY missing "
              "— skipping send", file=sys.stderr)
        return
    status = post(host, public, secret, batch)
    if status is not None:
        print(f"langfuse: sent (HTTP {status})", file=sys.stderr)


def cmd_ping() -> None:
    public, secret, host = resolve_creds()
    if not public or not secret:
        print("WARN: LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY missing — "
              "set them as shell env vars (never put them in the config file).")
        return
    ts = iso(now_utc())
    batch = [{"id": "aml-ping-trace-create", "type": "trace-create", "timestamp": ts,
              "body": {"id": "aml-ping", "name": "aml:ping",
                       "timestamp": ts, "tags": ["aml", "ping"]}}]
    status = post(host, public, secret, batch)
    if status is None:
        print(f"WARN: could not reach Langfuse ({host}) — check host/keys.")
    else:
        # Don't put host in the success message — avoids a self-hosted endpoint
        # leaking into chat logs (the failure WARN keeps host for debugging).
        print(f"OK: Langfuse connection verified (HTTP {status})")


def main() -> None:
    ap = argparse.ArgumentParser(prog="observe.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    td = sub.add_parser("task-done", help="task end — print metrics line (+ langfuse send)")
    td.add_argument("--since", required=True, help="task start time (ISO8601)")
    td.add_argument("--label", required=True, help="task number and name")
    td.add_argument("--feature", default=None, help="feature name (Langfuse sessionId)")
    td.add_argument("--note", default=None, help="one-line verification result")
    td.add_argument("--dry-run", action="store_true", help="print batch JSON instead of sending")
    sub.add_parser("ping", help="check Langfuse connection (for /aml:doctor)")
    args = ap.parse_args()
    if args.cmd == "task-done":
        cmd_task_done(args)
    else:
        cmd_ping()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — observability must never block impl
        print(f"metrics: unavailable ({exc})")
        sys.exit(0)
