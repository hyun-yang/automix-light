#!/usr/bin/env python3
"""observe.py — automix-light의 유일한 스크립트 (관측 전용, stdlib만).

태스크가 끝나면 /aml:go 가 호출한다:
  observe.py task-done --since <ISO8601> --label "<태스크>" \
      [--feature "<기능명>"] [--note "<검증 결과>"] [--dry-run]
→ 세션 transcript(~/.claude/projects/<인코딩된 cwd>/*.jsonl)에서 창(since→now)의
  모델별 토큰 사용량을 합산해 progress.md 에 붙일 "측정: …" 한 줄을 stdout 으로 낸다.
→ .aml/config.yaml 의 langfuse 가 "on" 이면 같은 데이터를 Langfuse 로 추가 전송한다
  (Task 2에서 구현; 자격증명은 env 전용).

불변 조건: 완전 fail-open — 어떤 런타임 실패도 경고 한 줄 후 exit 0.
관측 실패가 구현을 막아서는 안 된다. (argparse 사용 오류 exit 2만 예외.)
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

# 모델 계열별 단가 (USD/MTok, 입력/출력) — am pricing.py 와 동일한 표.
PRICING = {"opus": (5.0, 25.0), "fable": (10.0, 50.0),
           "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}
CACHE_WRITE_MULT = 1.25   # 캐시 쓰기 ≈ 입력 단가의 1.25배
CACHE_READ_MULT = 0.10    # 캐시 읽기 ≈ 입력 단가의 0.1배


# ── 시간/표기 유틸 ──────────────────────────────────────────────────────────

def parse_ts(ts) -> datetime | None:
    if not ts:
        return None
    s = str(ts).strip().replace("Z", "+00:00")
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)   # BSD date 의 +1000 → +10:00
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
        return f"{secs // 3600}시간 {secs % 3600 // 60}분"
    if secs >= 60:
        return f"{secs // 60}분 {secs % 60}초"
    return f"{secs}초"


# ── transcript 발견 + 집계 (am task-metrics.py 축약 이식) ───────────────────

def projects_root() -> Path:
    return Path(os.environ.get("AML_CLAUDE_PROJECTS_DIR")
                or os.path.expanduser("~/.claude/projects"))


def _dir_cwd(d: Path) -> str | None:
    """이 transcript 디렉터리에 기록된 realpath cwd (없으면 None)."""
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
    """현재 cwd 의 transcript 디렉터리. 인코딩(`[^A-Za-z0-9] → -`)이 손실형이라
    기록된 cwd 로 검증하고, 불일치·미발견이면 전체 스캔한다."""
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
    """창 [start, end] 안의 assistant usage 를 모델별로 합산.
    transcript 미발견 → None (측정 줄이 '수집 불가'로 렌더링된다)."""
    d = transcript_dir()
    if d is None:
        return None
    per: dict[str, dict] = {}
    start_epoch = start.timestamp()
    for f in d.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < start_epoch - 2:   # 창 이전에 끝난 파일 프루닝
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
                model = msg.get("model") or "?"   # 모델 미기록 레코드는 "?" 버킷 (비용 생략)
                tot = per.setdefault(model, {k: 0 for k in USAGE_FIELDS})
                for k in USAGE_FIELDS:
                    tot[k] += usage.get(k, 0) or 0
    return per


# ── 비용 ────────────────────────────────────────────────────────────────────

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


# ── 측정 줄 렌더링 ──────────────────────────────────────────────────────────

def measure_line(dur_secs: int, per: dict[str, dict] | None) -> str:
    if per is None:
        return "측정: 수집 불가 (세션 기록을 찾지 못함)"
    if not per:
        return f"측정: {humanize_dur(dur_secs)} · 토큰 기록 없음"
    items = sorted(per.items())
    costs = [cost_usd(m, t) for m, t in items]
    known = [c for c in costs if c is not None]
    total = sum(known) if known else None
    if len(items) == 1:
        m, t = items[0]
        line = (f"측정: {m} · {humanize_dur(dur_secs)}"
                f" · 토큰 입력 {humanize(t['input_tokens'])} / 출력 {humanize(t['output_tokens'])}"
                f" (캐시 읽기 {humanize(t['cache_read_input_tokens'])}"
                f" / 쓰기 {humanize(t['cache_creation_input_tokens'])})")
    else:
        parts = [f"{m}(입력 {humanize(t['input_tokens'])}/출력 {humanize(t['output_tokens'])})"
                 for m, t in items]
        line = f"측정: {humanize_dur(dur_secs)} · " + " + ".join(parts)
    if total is not None:
        line += f" · 예상 비용 {fmt_usd(total)}"
    return line


# ── Langfuse (opt-in, 기본 off — .aml/config.yaml 부재 = off) ───────────────

def config_get(key: str) -> str | None:
    """.aml/config.yaml 의 키를 first-match 로 읽는다 (am get_config 규약).
    파일은 평평한 2키(langfuse/langfuse_host)로 문서화되며,
    중첩·중복이 있어도 파일 내 첫 텍스트 일치가 이긴다."""
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
    """태스크 하나 → Langfuse ingestion 배치. id 는 label+since 기반으로 결정적."""
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
        print(f"langfuse: 전송 실패 ({exc}) — 계속 진행", file=sys.stderr)
        return None


# ── 커맨드 ──────────────────────────────────────────────────────────────────

def cmd_task_done(args) -> None:
    since = parse_ts(args.since)
    if since is None:
        print("측정: 수집 불가 (--since 시각을 읽지 못함)")
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
        print("langfuse: on 이지만 LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY 가 없어 "
              "전송 생략", file=sys.stderr)
        return
    status = post(host, public, secret, batch)
    if status is not None:
        print(f"langfuse: 전송됨 (HTTP {status})", file=sys.stderr)


def cmd_ping() -> None:
    public, secret, host = resolve_creds()
    if not public or not secret:
        print("WARN: LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY 가 없습니다 — "
              "셸 환경변수로 설정하세요 (config 파일에는 넣지 않습니다).")
        return
    ts = iso(now_utc())
    batch = [{"id": "aml-ping-trace-create", "type": "trace-create", "timestamp": ts,
              "body": {"id": "aml-ping", "name": "aml:ping",
                       "timestamp": ts, "tags": ["aml", "ping"]}}]
    status = post(host, public, secret, batch)
    if status is None:
        print(f"WARN: Langfuse 에 연결하지 못했습니다 ({host}) — 호스트/키를 확인하세요.")
    else:
        # 성공 메시지에는 host 를 넣지 않는다 — 자체 호스팅 endpoint 가
        # 대화 로그에 남는 것을 피한다 (실패 WARN 은 디버깅용으로 host 유지).
        print(f"OK: Langfuse 연결 확인 (HTTP {status})")


def main() -> None:
    ap = argparse.ArgumentParser(prog="observe.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    td = sub.add_parser("task-done", help="태스크 종료 — 측정 줄 출력 (+ langfuse 전송)")
    td.add_argument("--since", required=True, help="태스크 시작 시각 (ISO8601)")
    td.add_argument("--label", required=True, help="태스크 번호와 이름")
    td.add_argument("--feature", default=None, help="기능명 (Langfuse sessionId)")
    td.add_argument("--note", default=None, help="검증 결과 한 줄")
    td.add_argument("--dry-run", action="store_true", help="전송 대신 배치 JSON 출력")
    sub.add_parser("ping", help="Langfuse 연결 확인 (/aml:doctor 용)")
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
    except Exception as exc:  # noqa: BLE001 — 관측은 절대 구현을 막지 않는다
        print(f"측정: 수집 불가 ({exc})")
        sys.exit(0)
