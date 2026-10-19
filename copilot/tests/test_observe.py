"""test_observe.py — Copilot 판 observe.py 의 측정·요약 숫자 검사 (표준 라이브러리만).

사용법 (저장소 루트에서): python3 copilot/tests/test_observe.py
숫자를 미리 정한 가짜 세션 기록을 만들어, 구간 사용량과 요약이 기대값과 정확히 같은지 본다.
기록 모양은 2026-10-19 Copilot CLI 1.0.98 의 실제 events.jsonl 에서 숫자만 바꿔 옮겼다.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True   # 패키지 폴더에 __pycache__ 를 남기지 않는다 (설치 때 함께 복사됨)
HERE = Path(__file__).resolve().parent
OBSERVE = HERE.parent / "aml" / "scripts" / "observe.py"
spec = importlib.util.spec_from_file_location("observe", OBSERVE)
ob = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ob)

SID = "aaaaaaaa-0000-4000-8000-000000000001"
OTHER = "bbbbbbbb-0000-4000-8000-000000000002"

_n = 0


def rec(ts, model, fresh, cr, cw, out, reasoning=0, nano=None, uid=None, details=True):
    """usage_record 한 줄. 입력 = 캐시 안 된 입력 + 캐시 읽기 + 캐시 쓰기 (실제 기록과 같은 관계)."""
    global _n
    _n += 1
    u = {"model": model, "inputTokens": fresh + cr + cw, "outputTokens": out,
         "cacheReadTokens": cr, "cacheWriteTokens": cw, "reasoningTokens": reasoning, "cost": 1.0,
         "accounting": {"sourceSessionId": SID, "sequence": _n, "usageId": uid or f"u{_n}"}}
    cu = {}
    if details:
        cu["tokenDetails"] = [{"tokenType": "input", "tokenCount": fresh},
                              {"tokenType": "cache_read", "tokenCount": cr},
                              {"tokenType": "cache_write", "tokenCount": cw},
                              {"tokenType": "output", "tokenCount": out}]
    if nano is not None:
        cu["totalNanoAiu"] = nano
    u["copilotUsage"] = cu
    return {"type": "session.usage_record", "data": {"usage": u}, "id": f"e{_n}", "timestamp": ts}


def start(sid, version="1.0.98", at="2026-10-19T00:00:00.000Z"):
    return {"type": "session.start", "id": "s0", "timestamp": at,
            "data": {"sessionId": sid, "version": 1, "producer": "copilot-agent",
                     "copilotVersion": version, "startTime": at}}


def write_session(home: Path, sid: str, rows, with_start=True, version="1.0.98",
                  at="2026-10-19T00:00:00.000Z"):
    d = home / "session-state" / sid
    d.mkdir(parents=True, exist_ok=True)
    lines = ([start(sid, version, at)] if with_start else []) + rows
    (d / "events.jsonl").write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")


SINCE = "2026-10-19T00:10:00+00:00"
END = datetime(2026, 10, 19, 0, 20, tzinfo=timezone.utc)   # 10분 구간

# 구간 안: (캐시 안 된 입력 2000 + 400, 캐시 읽기 1000 + 600, 쓰기 300 + 0, 출력 300 + 200, 추론 50)
# AI 크레딧 0.12 + 0.10 = 0.22
BASE_ROWS = [
    rec("2026-10-19T00:05:00.000Z", "gpt-test", 9000, 0, 0, 900, nano=500_000_000),      # 시작 전 — 빼야 함
    rec("2026-10-19T00:12:00.000Z", "gpt-test", 2000, 1000, 300, 300, 50, nano=120_000_000, uid="dup"),
    rec("2026-10-19T00:12:00.000Z", "gpt-test", 2000, 1000, 300, 300, 50, nano=120_000_000, uid="dup"),  # 중복
    rec("2026-10-19T00:15:00.000Z", "gpt-test", 400, 600, 0, 200, nano=100_000_000),
    rec("2026-10-19T00:25:00.000Z", "gpt-test", 7000, 0, 0, 700, nano=900_000_000),      # 끝 이후 — 빼야 함
]
BASE_LINE = "측정: gpt-test · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k / 쓰기 300) · 비용 미산정 · AI 크레딧 0.22"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "copilot-home"
        self.proj = Path(self.tmp.name) / "proj"
        self.proj.mkdir()
        self._old = {k: os.environ.get(k) for k in ("COPILOT_HOME", "COPILOT_AGENT_SESSION_ID")}
        os.environ.update({"COPILOT_HOME": str(self.home), "COPILOT_AGENT_SESSION_ID": SID})
        self._cwd = os.getcwd()
        os.chdir(self.proj)

    def tearDown(self):
        os.chdir(self._cwd)
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def per(self):
        sid = ob.current_session_id()
        st, records = ob.read_events(ob.find_session_file(sid), sid)
        return ob.interval_usage(st, records, ob.parse_ts(SINCE), END)


class TestInterval(Base):
    def test_known_sum_and_duplicates(self):
        write_session(self.home, SID, BASE_ROWS)
        per = self.per()
        self.assertEqual(list(per), ["gpt-test"])
        t = per["gpt-test"]
        self.assertEqual((t["input_tokens"], t["cached_input_tokens"], t["cache_write_input_tokens"],
                          t["output_tokens"], t["reasoning_output_tokens"], t["nano_aiu"]),
                         (2400, 1600, 300, 500, 50, 220_000_000))

    def test_line_does_not_double_count_cache(self):
        write_session(self.home, SID, BASE_ROWS)
        self.assertEqual(ob.task_done_line(SINCE, end=END), BASE_LINE)

    def test_other_session_is_ignored(self):
        write_session(self.home, SID, BASE_ROWS)
        write_session(self.home, OTHER, [rec("2026-10-19T00:11:00.000Z", "gpt-other", 90000, 0, 0, 9000)])
        self.assertEqual(ob.task_done_line(SINCE, end=END), BASE_LINE)

    def test_no_session_id_means_no_record(self):
        write_session(self.home, SID, BASE_ROWS)
        os.environ.pop("COPILOT_AGENT_SESSION_ID")
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (지금 세션 번호를 알 수 없습니다)")

    def test_session_started_mid_task_is_no_record(self):
        write_session(self.home, SID, BASE_ROWS[3:4], at="2026-10-19T00:14:00.000Z")
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (할 일 도중에 세션이 바뀌었습니다)")

    def test_no_sessions_dir(self):
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (Copilot 세션 기록 폴더가 없습니다)")

    def test_session_file_missing(self):
        write_session(self.home, OTHER, BASE_ROWS)
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (지금 세션의 기록 파일을 찾지 못했습니다)")

    def test_unknown_format(self):
        write_session(self.home, SID, BASE_ROWS, with_start=False)
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (세션 기록의 형식을 알 수 없습니다)")

    def test_old_version_is_not_guessed(self):
        write_session(self.home, SID, BASE_ROWS, version="1.0.90")
        self.assertEqual(ob.task_done_line(SINCE, end=END),
                         "측정: 기록 없음 (확인하지 않은 Copilot CLI 버전의 기록입니다)")

    def test_inconsistent_numbers_are_not_guessed(self):
        bad = rec("2026-10-19T00:12:00.000Z", "gpt-test", 100, 0, 0, 10)
        bad["data"]["usage"]["copilotUsage"]["tokenDetails"][0]["tokenCount"] = 99   # 입력 합이 안 맞음
        write_session(self.home, SID, [bad])
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 기록 없음 (토큰 숫자의 관계가 예상과 다릅니다)")
        neg = rec("2026-10-19T00:12:00.000Z", "gpt-test", 0, 500, 0, 10, details=False)
        neg["data"]["usage"]["inputTokens"] = 100                                    # 캐시가 입력보다 큼
        write_session(self.home, SID, [neg])
        self.assertIn("기록 없음", ob.task_done_line(SINCE, end=END))

    def test_no_usage_in_interval_is_not_zero_cost(self):
        write_session(self.home, SID, BASE_ROWS[:1])
        self.assertEqual(ob.task_done_line(SINCE, end=END), "측정: 10분 0초 · 토큰 기록 없음")

    def test_missing_credit_is_not_written_as_zero(self):
        write_session(self.home, SID, [rec("2026-10-19T00:12:00.000Z", "gpt-test", 2000, 0, 0, 300)])
        self.assertEqual(ob.task_done_line(SINCE, end=END),
                         "측정: gpt-test · 10분 0초 · 토큰 입력 2.0k / 출력 300 (캐시 읽기 0 / 쓰기 0) · 비용 미산정")

    def test_multi_model(self):
        rows = [rec("2026-10-19T00:12:00.000Z", "gpt-a", 500, 500, 0, 100, nano=10_000_000),
                rec("2026-10-19T00:14:00.000Z", "gpt-b", 3000, 0, 0, 300, nano=20_000_000)]
        write_session(self.home, SID, rows)
        self.assertEqual(ob.task_done_line(SINCE, end=END),
                         "측정: 10분 0초 · gpt-a(입력 500/출력 100) + gpt-b(입력 3.0k/출력 300) · 비용 미산정 · AI 크레딧 0.03")


class TestCost(unittest.TestCase):
    TOK = {"input_tokens": 2_000_000, "cached_input_tokens": 1_000_000, "cache_write_input_tokens": 0,
           "output_tokens": 500_000, "reasoning_output_tokens": 200_000, "nano_aiu": None}

    def test_known_price_counts_cache_once(self):
        # 캐시 안 된 입력 2M × $2 + 캐시 1M × $0.5 + 출력 0.5M × $8 (추론은 출력 안에 있음)
        self.assertAlmostEqual(ob.cost_usd("gpt-test", self.TOK, {"gpt-test": (2.0, 0.5, 8.0)}), 8.5)

    def test_unknown_model_has_no_cost(self):
        self.assertIsNone(ob.cost_usd("gpt-unknown", self.TOK, {"gpt-test": (2.0, 0.5, 8.0)}))

    def test_cache_write_without_price_is_not_guessed(self):
        tok = dict(self.TOK, cache_write_input_tokens=10)
        self.assertIsNone(ob.cost_usd("gpt-test", tok, {"gpt-test": (2.0, 0.5, 8.0)}))


class TestSummary(unittest.TestCase):
    PROGRESS = """# 진행 기록
- <observe.py 출력을 그대로 — `측정: …` 한 줄: 모델 · 걸린 시간 · 토큰 · 예상 비용. 실패하면 `측정: 기록 없음`>
- 측정: claude-opus-5-5 · 4분 16초 · 토큰 입력 74 / 출력 65k (캐시 읽기 5.9M / 쓰기 105k) · 예상 비용 $5.23
- 측정: gpt-codex · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k) · 비용 미산정
- 측정: gpt-test · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k / 쓰기 300) · 비용 미산정 · AI 크레딧 0.22
- 측정: 1분 30초 · gpt-a(입력 500/출력 100) + gpt-b(입력 3.0k/출력 300) · 비용 미산정 · AI 크레딧 0.03
- 측정: 기록 없음 (지금 세션 번호를 알 수 없습니다)
"""

    def test_mixed_claude_codex_copilot_lines(self):
        self.assertEqual(ob.summarize_progress(self.PROGRESS), "\n".join([
            "요약: 작업 5개 · 총 25분 46초 · 토큰 대략 입력 8.4k / 출력 66.4k · 알려진 비용 합계 $5.23",
            "모델: claude-opus-5-5 1회 · gpt-a 1회 · gpt-b 1회 · gpt-codex 1회 · gpt-test 1회",
            "AI 크레딧 합계: 0.25 (Copilot 이 기록한 사용량 — 달러 비용과 따로 셈)",
            "비용 미산정 작업: 3개 (가격을 확인하지 못한 모델 — 0 으로 치지 않음)",
            "측정 없는 작업: 1개"]))

    def test_empty(self):
        self.assertEqual(ob.summarize_progress("# 진행 기록\n"), "요약: 측정 줄이 아직 없습니다")


class TestCli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(OBSERVE), *args], cwd=self.proj,
                              env=dict(os.environ), capture_output=True, text=True)

    def test_start_then_done_round_trip(self):
        write_session(self.home, SID, BASE_ROWS[:1])
        r = self.run_cli("task-start", "--label", "1.1 시험")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("시작: "), r.stdout)
        self.assertEqual(r.stderr, "")                    # 기록을 읽을 수 있으면 경고 없음
        r = self.run_cli("task-done", "--since", r.stdout.split("시작: ")[1].strip(), "--label", "1.1 시험")
        self.assertEqual(r.returncode, 0)
        self.assertIn("토큰 기록 없음", r.stdout)        # 시작 뒤에 쓴 토큰이 없음 (0 비용으로 표시 안 함)
        self.assertFalse((self.proj / ".aml").exists())   # 프로젝트에 아무것도 남기지 않는다

    def test_bad_input_never_fails(self):
        os.environ.pop("COPILOT_AGENT_SESSION_ID")
        for args in (("task-done", "--since", "어제"), ("task-done", "--since", SINCE),
                     ("task-start",), ("check",), ("summary", "없는파일.md")):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, (args, r.stderr))
        self.assertIn("기록 없음", self.run_cli("task-done", "--since", SINCE).stdout)
        self.assertIn("기록 없음", self.run_cli("check").stdout)

    def test_real_shape_from_copilot_1_0_98(self):
        # 2026-10-19 실제 기록의 숫자 그대로 (입력 15264 = 7968 + 캐시 7296, AI 크레딧 0.175752)
        write_session(self.home, SID, [rec("2026-10-19T00:12:00.000Z", "mai-code-1.1-flash",
                                           7968, 7296, 0, 15, nano=175_752_000)])
        self.assertEqual(ob.task_done_line(SINCE, end=END),
                         "측정: mai-code-1.1-flash · 10분 0초 · 토큰 입력 8.0k / 출력 15 (캐시 읽기 7.3k / 쓰기 0) · 비용 미산정 · AI 크레딧 0.18")


if __name__ == "__main__":
    unittest.main(verbosity=1)
