#!/usr/bin/env python3
"""observe.py — aml (Copilot CLI 판) 측정 스크립트. 파이썬 표준 라이브러리만 쓴다.

  task-start --label L          할 일 시작: 시작 시각을 찍는다
  task-done  --since T --label L [--feature F] [--note N]
                                할 일 끝: 지금 세션의 구간 사용량을 "측정: …" 한 줄로 출력
  summary    <progress.md>      progress.md 의 측정 줄 합산 (Claude/Codex/Copilot 줄이 섞여도 됨)
  check                         지금 세션 사용량을 읽을 수 있는지 한 줄로 알림 (/aml:doctor 용)

규칙 (references/telemetry.md):
  - 세션은 Copilot 이 셸에 넘겨주는 COPILOT_AGENT_SESSION_ID(또는 --session) 로만 고른다. 같은 폴더의 다른 세션을 고르지 않는다.
  - Copilot 은 모델을 부를 때마다 그 한 번의 사용량을 session.usage_record 로 남긴다 — 구간 사용량은 그 기록들의 합이다.
  - 입력 토큰 = 캐시 안 된 입력 + 캐시 읽기 + 캐시 쓰기. 이 관계가 맞지 않으면 추측하지 않고 '기록 없음'.
  - 단가를 확인한 모델만 달러 비용을 계산한다. 나머지는 '비용 미산정' (0 으로 치지 않는다).
    Copilot 이 직접 기록한 AI 크레딧은 달러와 섞지 않고 따로 적는다.
측정이 구현을 막아서는 안 된다 — 무슨 일이 있어도 종료 코드 0 (argparse 사용법 오류만 2).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_output_tokens")

# 모델별 단가 (USD / 100만 토큰): (입력, 캐시 읽기 입력, 출력).
# 출처와 확인일을 references/telemetry.md 에 적은 모델만 넣는다. 지금은 확인된 단가가 없다.
PRICING: dict[str, tuple[float, float, float]] = {}

# 토큰 숫자의 관계를 실제 기록으로 확인한 가장 낮은 Copilot CLI 버전 (references/telemetry.md).
MIN_VERSION = (1, 0, 98)

NANO = 1_000_000_000   # totalNanoAiu 를 AI 크레딧으로 바꾸는 값 (Copilot 화면의 "AI Credits" 와 같음)


class NoRecord(Exception):
    """측정할 수 없음 — 메시지가 '측정: 기록 없음 (…)' 의 괄호 안에 들어간다."""


# ── 시각 / 표기 ────────────────────────────────────────────────────────────

def parse_ts(ts) -> datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def humanize(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def humanize_dur(secs: int) -> str:
    h, rem = divmod(max(0, secs), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}시간 {m}분"
    if m:
        return f"{m}분 {s}초"
    return f"{s}초"


def fmt_usd(c: float) -> str:
    return f"${c:.4f}" if c < 0.01 else f"${c:.2f}"


def fmt_credit(c: float) -> str:
    return f"{c:.4f}" if c < 0.01 else f"{c:.2f}"


# ── 세션 찾기 ─────────────────────────────────────────────────────────────

def sessions_dir() -> Path:
    home = os.environ.get("COPILOT_HOME") or str(Path.home() / ".copilot")
    return Path(home) / "session-state"


def current_session_id(explicit: str | None = None) -> str:
    sid = explicit or os.environ.get("COPILOT_AGENT_SESSION_ID")
    if not sid:
        raise NoRecord("지금 세션 번호를 알 수 없습니다")
    return sid.strip()


def find_session_file(sid: str) -> Path:
    root = sessions_dir()
    if not root.is_dir():
        raise NoRecord("Copilot 세션 기록 폴더가 없습니다")
    path = root / sid / "events.jsonl"
    if "/" in sid or not path.is_file():
        raise NoRecord("지금 세션의 기록 파일을 찾지 못했습니다")
    return path


def version_tuple(v) -> tuple[int, ...] | None:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else None


def to_usage(u: dict) -> dict:
    """usage_record 한 줄을 측정용 숫자로 바꾼다. 숫자 관계가 맞지 않으면 NoRecord."""
    try:
        inp = int(u["inputTokens"])
        out = int(u["outputTokens"])
        cr = int(u.get("cacheReadTokens") or 0)
        cw = int(u.get("cacheWriteTokens") or 0)
        rs = int(u.get("reasoningTokens") or 0)
    except (KeyError, TypeError, ValueError):
        raise NoRecord("토큰 숫자의 관계가 예상과 다릅니다")
    fresh = inp - cr - cw
    details = {}
    for d in (u.get("copilotUsage") or {}).get("tokenDetails") or []:
        if isinstance(d, dict):
            details[d.get("tokenType")] = d.get("tokenCount")
    if (min(inp, out, cr, cw, rs) < 0 or fresh < 0 or rs > out
            or ("input" in details and details["input"] != fresh)):
        raise NoRecord("토큰 숫자의 관계가 예상과 다릅니다")
    return {"input_tokens": fresh, "cached_input_tokens": cr, "cache_write_input_tokens": cw,
            "output_tokens": out, "reasoning_output_tokens": rs}


def read_events(path: Path, sid: str):
    """세션 파일에서 (세션 시작 시각, [(시각, 모델, 구분 키, 사용량 원본)]) 을 돌려준다."""
    start = None
    meta_ok = False
    version = None
    records = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            kind = obj.get("type")
            data = obj.get("data") or {}
            if not isinstance(data, dict):
                continue
            if kind == "session.start":
                meta_ok = data.get("sessionId") == sid
                version = version_tuple(data.get("copilotVersion"))
                start = parse_ts(data.get("startTime"))
            elif kind == "session.usage_record":
                u = data.get("usage")
                ts = parse_ts(obj.get("timestamp"))
                if not isinstance(u, dict) or ts is None:
                    continue
                key = (u.get("accounting") or {}).get("usageId") or obj.get("id")
                records.append((ts, u.get("model") or "?", key, u))
    if not meta_ok:
        raise NoRecord("세션 기록의 형식을 알 수 없습니다")
    if version is None or version < MIN_VERSION:
        raise NoRecord("확인하지 않은 Copilot CLI 버전의 기록입니다")
    return start, records


# ── 구간 사용량 ────────────────────────────────────────────────────────────

def interval_usage(start, records, since: datetime, end: datetime) -> dict[str, dict]:
    """since 뒤, end 까지의 usage_record 를 모델별로 더한다. 같은 기록이 두 번 있으면 한 번만 센다.

    세션이 할 일 도중에 시작됐다면 앞 세션에서 쓴 양을 알 수 없으니 '기록 없음'."""
    if start is None or start > since:
        raise NoRecord("할 일 도중에 세션이 바뀌었습니다")
    per: dict[str, dict] = {}
    seen = set()
    for ts, model, key, raw in records:
        if ts <= since or ts > end:
            continue
        if key is not None:
            if key in seen:
                continue                           # 중복 기록
            seen.add(key)
        u = to_usage(raw)
        tot = per.setdefault(model, dict({k: 0 for k in FIELDS}, nano_aiu=0))
        for k in FIELDS:
            tot[k] += u[k]
        nano = (raw.get("copilotUsage") or {}).get("totalNanoAiu")
        if isinstance(nano, (int, float)) and tot["nano_aiu"] is not None:
            tot["nano_aiu"] += nano
        else:
            tot["nano_aiu"] = None                 # 하나라도 모르면 그 모델의 크레딧은 적지 않는다
    return per


def cost_usd(model: str, tok: dict, pricing: dict | None = None) -> float | None:
    """단가를 아는 모델만 계산. '입력' 은 이미 캐시 안 된 입력이다."""
    table = PRICING if pricing is None else pricing
    price = table.get(model.strip().lower())
    if price is None or tok.get("cache_write_input_tokens"):
        return None                                # 캐시 쓰기 단가는 확인하지 않았다
    inp, cached, out = price
    return (tok["input_tokens"] / 1e6 * inp + tok["cached_input_tokens"] / 1e6 * cached
            + tok["output_tokens"] / 1e6 * out)


def measure_line(dur_secs: int, per: dict[str, dict], pricing: dict | None = None) -> str:
    """Claude 판 측정 줄과 같은 모양. '입력' 은 캐시 안 된 입력, '캐시 읽기 / 쓰기' 는 따로."""
    if not per:
        return f"측정: {humanize_dur(dur_secs)} · 토큰 기록 없음"
    items = sorted(per.items())
    costs = [cost_usd(m, t, pricing) for m, t in items]
    if len(items) == 1:
        m, t = items[0]
        line = (f"측정: {m} · {humanize_dur(dur_secs)}"
                f" · 토큰 입력 {humanize(t['input_tokens'])} / 출력 {humanize(t['output_tokens'])}"
                f" (캐시 읽기 {humanize(t['cached_input_tokens'])}"
                f" / 쓰기 {humanize(t['cache_write_input_tokens'])})")
    else:
        parts = [f"{m}(입력 {humanize(t['input_tokens'])}/출력 {humanize(t['output_tokens'])})"
                 for m, t in items]
        line = f"측정: {humanize_dur(dur_secs)} · " + " + ".join(parts)
    known = [c for c in costs if c is not None]
    if known and len(known) == len(costs):
        line += f" · 예상 비용 {fmt_usd(sum(known))}"
    elif known:
        line += f" · 예상 비용 {fmt_usd(sum(known))} (일부 비용 미산정)"
    else:
        line += " · 비용 미산정"
    nanos = [t["nano_aiu"] for _m, t in items]
    if all(n is not None for n in nanos):
        line += f" · AI 크레딧 {fmt_credit(sum(nanos) / NANO)}"
    return line


# ── 진행 기록 요약 (progress.md 의 측정 줄 합산) ─────────────────────────────

_DUR_H = re.compile(r"(\d+)시간")
_DUR_M = re.compile(r"(\d+)분")
_DUR_S = re.compile(r"(\d+)초")
_COST = re.compile(r"예상 비용\s*\$([0-9]+(?:\.[0-9]+)?)")
_CREDIT = re.compile(r"AI 크레딧\s*([0-9]+(?:\.[0-9]+)?)")
_TOK_IN = re.compile(r"입력\s*([0-9]+(?:\.[0-9]+)?)([kM]?)")
_TOK_OUT = re.compile(r"출력\s*([0-9]+(?:\.[0-9]+)?)([kM]?)")
_MODEL_MULTI = re.compile(r"([A-Za-z][A-Za-z0-9._-]*)\(입력")
_MODEL_ONE = re.compile(r"^([A-Za-z][A-Za-z0-9._-]*)\s+·")


def unhumanize(num: str, unit: str) -> int:
    v = float(num)
    if unit == "k":
        v *= 1_000
    elif unit == "M":
        v *= 1_000_000
    return int(round(v))


def summarize_progress(text: str) -> str:
    tasks = untracked = no_cost = secs = tok_in = tok_out = 0
    cost = credit = 0.0
    have_cost = have_credit = False
    models: dict[str, int] = {}
    for raw in text.splitlines():
        at = raw.find("측정:")
        if at < 0:
            continue
        line = raw[at + len("측정:"):].strip()
        if line.startswith("기록 없음"):
            tasks += 1
            untracked += 1
            continue
        hits = [rx.search(line) for rx in (_DUR_H, _DUR_M, _DUR_S)]
        if not any(hits):
            continue  # 걸린 시간이 없으면 진짜 측정 줄이 아니다 (템플릿 안내문 등)
        tasks += 1
        for m, mult in zip(hits, (3600, 60, 1)):
            if m:
                secs += int(m.group(1)) * mult
        m = _COST.search(line)
        if m:
            cost += float(m.group(1))
            have_cost = True
        m = _CREDIT.search(line)
        if m:
            credit += float(m.group(1))
            have_credit = True
        if "미산정" in line:
            no_cost += 1
        for num, unit in _TOK_IN.findall(line):
            tok_in += unhumanize(num, unit)
        for num, unit in _TOK_OUT.findall(line):
            tok_out += unhumanize(num, unit)
        found = _MODEL_MULTI.findall(line)
        if not found:
            one = _MODEL_ONE.match(line)
            found = [one.group(1)] if one else []
        for name in found:
            models[name] = models.get(name, 0) + 1
    if tasks == 0:
        return "요약: 측정 줄이 아직 없습니다"
    parts = [f"요약: 작업 {tasks}개", f"총 {humanize_dur(secs)}"]
    if tok_in or tok_out:
        parts.append(f"토큰 대략 입력 {humanize(tok_in)} / 출력 {humanize(tok_out)}")
    if have_cost:
        parts.append(f"알려진 비용 합계 {fmt_usd(cost)}")
    out = " · ".join(parts)
    if models:
        ranked = sorted(models.items(), key=lambda kv: (-kv[1], kv[0]))
        out += "\n모델: " + " · ".join(f"{m} {n}회" for m, n in ranked)
    if have_credit:
        out += f"\nAI 크레딧 합계: {fmt_credit(credit)} (Copilot 이 기록한 사용량 — 달러 비용과 따로 셈)"
    if no_cost:
        out += f"\n비용 미산정 작업: {no_cost}개 (가격을 확인하지 못한 모델 — 0 으로 치지 않음)"
    if untracked:
        out += f"\n측정 없는 작업: {untracked}개"
    return out


# ── 명령 ──────────────────────────────────────────────────────────────────

def task_done_line(since_s: str, session: str | None = None, end: datetime | None = None) -> str:
    since = parse_ts(since_s)
    if since is None:
        return "측정: 기록 없음 (--since 시각을 읽지 못했습니다)"
    end = end or now_utc()
    dur = max(0, int((end - since).total_seconds()))
    try:
        sid = current_session_id(session)
        start, records = read_events(find_session_file(sid), sid)
        per = interval_usage(start, records, since, end)
    except NoRecord as exc:
        return f"측정: 기록 없음 ({exc})"
    except OSError as exc:
        return f"측정: 기록 없음 (세션 기록을 읽지 못했습니다: {exc.__class__.__name__})"
    return measure_line(dur, per)


def cmd_task_start(args) -> None:
    print(f"시작: {now_utc().astimezone().isoformat(timespec='seconds')}")
    try:
        sid = current_session_id(args.session)
        read_events(find_session_file(sid), sid)
    except (NoRecord, OSError) as exc:
        print(f"측정 준비: 사용량을 읽을 수 없어 끝날 때 '기록 없음' 이 남습니다 ({exc})", file=sys.stderr)


def cmd_task_done(args) -> None:
    print(task_done_line(args.since, args.session))


def cmd_summary(args) -> None:
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        print(f"요약: {path} 를 읽지 못했습니다")
        return
    print(summarize_progress(text))


def cmd_check(args) -> None:
    try:
        sid = current_session_id(args.session)
        read_events(find_session_file(sid), sid)
    except (NoRecord, OSError) as exc:
        print(f"측정: 지금은 사용량을 읽을 수 없어 '측정: 기록 없음' 으로 남습니다 ({exc}). 작업은 그대로 진행됩니다")
        return
    print("측정: 지금 세션의 사용량을 읽을 수 있습니다 (달러 비용은 단가를 확인한 모델만, AI 크레딧은 Copilot 기록 그대로)")


def main() -> None:
    # Windows 에서는 출력 인코딩이 UTF-8 이 아니라 한글을 찍다가 멈춘다 — 출력만 UTF-8 로 맞춘다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="observe.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ts = sub.add_parser("task-start", help="할 일 시작 — 시작 시각 출력")
    ts.add_argument("--label", default="task")
    ts.add_argument("--session")
    td = sub.add_parser("task-done", help="할 일 끝 — 측정 줄 출력")
    td.add_argument("--since", required=True)
    td.add_argument("--label", default="task")
    td.add_argument("--feature")
    td.add_argument("--note")
    td.add_argument("--session")
    sm = sub.add_parser("summary", help="progress.md 의 측정 줄 합산 (/aml:status 용)")
    sm.add_argument("path")
    ck = sub.add_parser("check", help="사용량을 읽을 수 있는지 (/aml:doctor 용)")
    ck.add_argument("--session")
    args = ap.parse_args()
    handler = {"task-start": cmd_task_start, "task-done": cmd_task_done,
               "summary": cmd_summary, "check": cmd_check}[args.cmd]
    try:
        handler(args)
    except Exception as exc:  # noqa: BLE001 — 측정은 무슨 일이 있어도 작업을 막지 않는다
        if args.cmd == "task-done":
            print(f"측정: 기록 없음 ({exc.__class__.__name__})")
        else:
            print(f"측정 스크립트 오류: {exc.__class__.__name__}", file=sys.stderr)


if __name__ == "__main__":
    main()
