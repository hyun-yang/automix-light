#!/usr/bin/env python3
"""observe.py — aml (Codex 판) 측정 스크립트. 파이썬 표준 라이브러리만 쓴다.

  task-start --label L          할 일 시작: 시작 시각을 찍고, 지금 세션의 누적 사용량을 .aml/ 에 저장
  task-done  --since T --label L [--feature F] [--note N]
                                할 일 끝: 지금 세션의 구간 사용량을 "측정: …" 한 줄로 출력
  summary    <progress.md>      progress.md 의 측정 줄 합산 (Claude/Codex 줄이 섞여도 됨)
  check                         지금 세션 사용량을 읽을 수 있는지 한 줄로 알림 (aml-doctor 용)

규칙 (references/telemetry.md):
  - 세션은 Codex 가 넘겨주는 CODEX_THREAD_ID(또는 --session) 로만 고른다. 같은 폴더의 다른 세션을 고르지 않는다.
  - 구간 사용량 = 끝 누적값 − 시작 누적값. 시작값을 모르면 세션 전체 값을 대신 쓰지 않고 '기록 없음'.
  - 입력 토큰에는 캐시 읽기가 들어 있고, 출력 토큰에는 추론 토큰이 들어 있다 — 따로 더하지 않는다.
  - 단가를 확인한 모델만 비용을 계산한다. 나머지는 '비용 미산정' (0 으로 치지 않는다).
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
          "output_tokens", "reasoning_output_tokens", "total_tokens")

# 모델별 단가 (USD / 100만 토큰): (입력, 캐시 읽기 입력, 출력).
# 출처와 확인일을 references/telemetry.md 에 적은 모델만 넣는다. 지금은 확인된 단가가 없다.
PRICING: dict[str, tuple[float, float, float]] = {}

START_FILE = Path(".aml") / "codex-measure-start.json"

# 토큰 숫자의 관계를 실제 기록으로 확인한 가장 낮은 Codex 버전 (references/telemetry.md).
# 이보다 옛 기록(0.136 이하)은 추론 토큰이 출력 밖에 따로 있는 등 뜻이 달랐다.
MIN_VERSION = (0, 144, 0)


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


# ── 세션 찾기 ─────────────────────────────────────────────────────────────

def sessions_dir() -> Path:
    home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return Path(home) / "sessions"


def current_session_id(explicit: str | None = None) -> str:
    sid = explicit or os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
    if not sid:
        raise NoRecord("지금 세션 번호를 알 수 없습니다")
    return sid.strip()


def find_session_file(sid: str) -> Path:
    root = sessions_dir()
    if not root.is_dir():
        raise NoRecord("Codex 세션 기록 폴더가 없습니다")
    hits = sorted(root.rglob(f"rollout-*{sid}.jsonl"))
    if len(hits) != 1:
        raise NoRecord("지금 세션의 기록 파일을 찾지 못했습니다" if not hits
                       else "같은 세션 번호의 기록 파일이 여러 개입니다")
    return hits[0]


def version_tuple(v) -> tuple[int, ...] | None:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v or "")
    return tuple(int(x) for x in m.groups()) if m else None


def consistent(u: dict) -> bool:
    """입력 ⊇ 캐시 읽기, 출력 ⊇ 추론, 전체 = 입력 + 출력 — 이 관계가 맞을 때만 계산한다."""
    return (u["cached_input_tokens"] <= u["input_tokens"]
            and u["reasoning_output_tokens"] <= u["output_tokens"]
            and u["total_tokens"] == u["input_tokens"] + u["output_tokens"])


def read_events(path: Path, sid: str) -> list[tuple[datetime, str, dict]]:
    """세션 파일에서 (시각, 모델, 누적 사용량) 목록을 시간 순서로 돌려준다."""
    events: list[tuple[datetime, str, dict]] = []
    meta_ok = False
    version = None
    model = "?"
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            kind = obj.get("type")
            body = obj.get("payload") or {}
            if not isinstance(body, dict):
                continue
            if kind == "session_meta":
                meta_ok = (body.get("id") or body.get("session_id")) == sid
                version = version_tuple(body.get("cli_version"))
            elif kind == "turn_context":
                model = body.get("model") or "?"
            elif kind == "event_msg" and body.get("type") == "token_count":
                info = body.get("info") or {}
                tot = info.get("total_token_usage")
                ts = parse_ts(obj.get("timestamp"))
                if not isinstance(tot, dict) or ts is None:
                    continue
                try:
                    usage = {k: int(tot.get(k) or 0) for k in FIELDS}
                except (TypeError, ValueError):
                    continue
                events.append((ts, model, usage))
    if not meta_ok:
        raise NoRecord("세션 기록의 형식을 알 수 없습니다")
    if version is None or version < MIN_VERSION:
        raise NoRecord("확인하지 않은 Codex 버전의 기록입니다")
    return events


# ── 구간 사용량 ────────────────────────────────────────────────────────────

def interval_usage(events, since: datetime, end: datetime,
                   baseline: dict | None = None) -> dict[str, dict]:
    """since 직전 누적값(없으면 baseline)부터 end 까지 늘어난 양을 모델별로 합한다.

    같은 누적값이 다시 찍힌 것(중복)은 0 으로 지나가고, 누적값이 줄어들면
    카운터가 처음부터 다시 센 것으로 보고 새 값을 그대로 더한다."""
    prev = None
    for ts, _model, usage in events:
        if ts <= since:
            prev = usage
    if prev is None:
        prev = baseline
    if prev is None:
        raise NoRecord("구간 시작 누적값이 없습니다")
    if not consistent(prev):
        raise NoRecord("토큰 숫자의 관계가 예상과 다릅니다")
    per: dict[str, dict] = {}
    for ts, model, usage in events:
        if ts <= since or ts > end:
            continue
        if not consistent(usage):
            raise NoRecord("토큰 숫자의 관계가 예상과 다릅니다")
        if usage["total_tokens"] < prev["total_tokens"]:
            inc = dict(usage)                      # 누적값 초기화 — 0 부터 다시 셈
        else:
            inc = {k: max(0, usage[k] - prev[k]) for k in FIELDS}
        prev = usage
        if not inc["total_tokens"]:
            continue                               # 중복 이벤트
        tot = per.setdefault(model, {k: 0 for k in FIELDS})
        for k in FIELDS:
            tot[k] += inc[k]
    return per


def cost_usd(model: str, tok: dict, pricing: dict | None = None) -> float | None:
    """단가를 아는 모델만 계산. 입력 = 캐시 안 된 입력 + 캐시 읽기 (입력 안에 캐시가 들어 있음)."""
    table = PRICING if pricing is None else pricing
    price = table.get(model.strip().lower())
    if price is None or tok.get("cache_write_input_tokens"):
        return None                                # 캐시 쓰기 단가는 확인하지 않았다
    inp, cached, out = price
    fresh = max(0, tok["input_tokens"] - tok["cached_input_tokens"])
    return (fresh / 1e6 * inp + tok["cached_input_tokens"] / 1e6 * cached
            + tok["output_tokens"] / 1e6 * out)


def measure_line(dur_secs: int, per: dict[str, dict], pricing: dict | None = None) -> str:
    """Claude 판 측정 줄과 같은 모양. '입력' 은 캐시 안 된 입력, '캐시 읽기' 는 따로."""
    if not per:
        return f"측정: {humanize_dur(dur_secs)} · 토큰 기록 없음"
    items = sorted(per.items())
    costs = [cost_usd(m, t, pricing) for m, t in items]

    def fresh(t):
        return max(0, t["input_tokens"] - t["cached_input_tokens"])

    if len(items) == 1:
        m, t = items[0]
        line = (f"측정: {m} · {humanize_dur(dur_secs)}"
                f" · 토큰 입력 {humanize(fresh(t))} / 출력 {humanize(t['output_tokens'])}"
                f" (캐시 읽기 {humanize(t['cached_input_tokens'])})")
    else:
        parts = [f"{m}(입력 {humanize(fresh(t))}/출력 {humanize(t['output_tokens'])})"
                 for m, t in items]
        line = f"측정: {humanize_dur(dur_secs)} · " + " + ".join(parts)
    known = [c for c in costs if c is not None]
    if known and len(known) == len(costs):
        line += f" · 예상 비용 {fmt_usd(sum(known))}"
    elif known:
        line += f" · 예상 비용 {fmt_usd(sum(known))} (일부 비용 미산정)"
    else:
        line += " · 비용 미산정"
    return line


# ── 진행 기록 요약 (progress.md 의 측정 줄 합산) ─────────────────────────────

_DUR_H = re.compile(r"(\d+)시간")
_DUR_M = re.compile(r"(\d+)분")
_DUR_S = re.compile(r"(\d+)초")
_COST = re.compile(r"예상 비용\s*\$([0-9]+(?:\.[0-9]+)?)")
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
    cost = 0.0
    have_cost = False
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
    if no_cost:
        out += f"\n비용 미산정 작업: {no_cost}개 (가격을 확인하지 못한 모델 — 0 으로 치지 않음)"
    if untracked:
        out += f"\n측정 없는 작업: {untracked}개"
    return out


# ── 명령 ──────────────────────────────────────────────────────────────────

def cmd_task_start(args) -> None:
    start = now_utc().astimezone()
    print(f"시작: {start.isoformat(timespec='seconds')}")
    try:
        sid = current_session_id(args.session)
        events = read_events(find_session_file(sid), sid)
    except (NoRecord, OSError) as exc:
        print(f"측정 준비: 건너뜀 ({exc})", file=sys.stderr)
        return
    snap = {"label": args.label, "session": sid, "since": start.isoformat(),
            "usage": events[-1][2] if events else None}
    try:
        START_FILE.parent.mkdir(parents=True, exist_ok=True)
        START_FILE.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        print(f"측정 준비: 시작값 저장 실패 ({exc})", file=sys.stderr)


def load_baseline(label: str, sid: str) -> dict | None:
    try:
        snap = json.loads(START_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if snap.get("label") != label or snap.get("session") != sid:
        return None
    usage = snap.get("usage")
    return usage if isinstance(usage, dict) and all(k in usage for k in FIELDS) else None


def task_done_line(since_s: str, label: str, session: str | None = None,
                   end: datetime | None = None) -> str:
    since = parse_ts(since_s)
    if since is None:
        return "측정: 기록 없음 (--since 시각을 읽지 못했습니다)"
    end = end or now_utc()
    dur = max(0, int((end - since).total_seconds()))
    try:
        sid = current_session_id(session)
        events = read_events(find_session_file(sid), sid)
        per = interval_usage(events, since, end, load_baseline(label, sid))
    except NoRecord as exc:
        return f"측정: 기록 없음 ({exc})"
    except OSError as exc:
        return f"측정: 기록 없음 (세션 기록을 읽지 못했습니다: {exc.__class__.__name__})"
    return measure_line(dur, per)


def cmd_task_done(args) -> None:
    print(task_done_line(args.since, args.label, args.session))
    try:
        START_FILE.unlink()
    except OSError:
        pass


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
    print("측정: 지금 세션의 사용량을 읽을 수 있습니다 (비용은 단가를 확인한 모델만 계산)")


def main() -> None:
    ap = argparse.ArgumentParser(prog="observe.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ts = sub.add_parser("task-start", help="할 일 시작 — 시작 시각과 시작 누적값 저장")
    ts.add_argument("--label", default="task")
    ts.add_argument("--session")
    td = sub.add_parser("task-done", help="할 일 끝 — 측정 줄 출력")
    td.add_argument("--since", required=True)
    td.add_argument("--label", default="task")
    td.add_argument("--feature")
    td.add_argument("--note")
    td.add_argument("--session")
    sm = sub.add_parser("summary", help="progress.md 의 측정 줄 합산 (aml-status 용)")
    sm.add_argument("path")
    ck = sub.add_parser("check", help="사용량을 읽을 수 있는지 (aml-doctor 용)")
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
