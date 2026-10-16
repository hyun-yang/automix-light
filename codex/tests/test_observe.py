"""test_observe.py — Codex 판 observe.py 의 측정·요약 숫자 검사 (표준 라이브러리만).

사용법 (저장소 루트에서): python3 codex/tests/test_observe.py
숫자를 미리 정한 가짜 세션 기록을 만들어, 구간 사용량과 요약이 기대값과 정확히 같은지 본다.
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

SID = "01aaaaaa-0000-7000-8000-000000000001"
OTHER = "01bbbbbb-0000-7000-8000-000000000002"
CWD = "/work/project"


def usage(inp, cached, out, reasoning=0, cache_write=0):
    return {"input_tokens": inp, "cached_input_tokens": cached,
            "cache_write_input_tokens": cache_write, "output_tokens": out,
            "reasoning_output_tokens": reasoning, "total_tokens": inp + out}


def tc(ts, u):
    return {"timestamp": ts, "type": "event_msg",
            "payload": {"type": "token_count", "info": {"total_token_usage": u, "last_token_usage": u}}}


def ctx(ts, model):
    return {"timestamp": ts, "type": "turn_context", "payload": {"cwd": CWD, "model": model}}


def meta(sid, version="0.163.0"):
    return {"timestamp": "2026-10-17T00:00:00Z", "type": "session_meta",
            "payload": {"id": sid, "session_id": sid, "cwd": CWD, "cli_version": version}}


def write_session(home: Path, sid: str, rows, with_meta=True, version="0.163.0"):
    d = home / "sessions" / "2026" / "10" / "17"
    d.mkdir(parents=True, exist_ok=True)
    lines = ([meta(sid, version)] if with_meta else []) + rows
    (d / f"rollout-2026-10-17T00-00-00-{sid}.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")


SINCE = "2026-10-17T00:10:00+00:00"
END = datetime(2026, 10, 17, 0, 20, tzinfo=timezone.utc)   # 10분 구간

# 기본 세션: 시작 전 누적 (1000/400/100) → 끝 (5000/2000/600, 추론 200)
# 구간 증가: 입력 4000 (캐시 1600 → 캐시 안 된 입력 2400) / 출력 500
BASE_ROWS = [
    ctx("2026-10-17T00:01:00Z", "gpt-test"),
    tc("2026-10-17T00:05:00Z", usage(1000, 400, 100)),
    tc("2026-10-17T00:12:00Z", usage(3000, 1000, 300)),
    tc("2026-10-17T00:12:00Z", usage(3000, 1000, 300)),      # 중복 이벤트
    tc("2026-10-17T00:15:00Z", usage(5000, 2000, 600, 200)),
    tc("2026-10-17T00:25:00Z", usage(9000, 3000, 900)),      # 구간 끝 이후 — 빼야 함
]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "codex-home"
        self.proj = Path(self.tmp.name) / "proj"
        self.proj.mkdir()
        self.env = {"CODEX_HOME": str(self.home), "CODEX_THREAD_ID": SID}
        self._old = {k: os.environ.get(k) for k in ("CODEX_HOME", "CODEX_THREAD_ID", "CODEX_SESSION_ID")}
        os.environ.update(self.env)
        os.environ.pop("CODEX_SESSION_ID", None)
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
        events = ob.read_events(ob.find_session_file(sid), sid)
        return ob.interval_usage(events, ob.parse_ts(SINCE), END, ob.load_baseline("t", sid))


class TestInterval(Base):
    def test_known_difference_and_duplicates(self):
        write_session(self.home, SID, BASE_ROWS)
        per = self.per()
        self.assertEqual(list(per), ["gpt-test"])
        t = per["gpt-test"]
        self.assertEqual((t["input_tokens"], t["cached_input_tokens"], t["output_tokens"],
                          t["reasoning_output_tokens"], t["total_tokens"]),
                         (4000, 1600, 500, 200, 4500))

    def test_line_does_not_double_count_cache(self):
        write_session(self.home, SID, BASE_ROWS)
        line = ob.task_done_line(SINCE, "t", end=END)
        self.assertEqual(line, "측정: gpt-test · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k) · 비용 미산정")

    def test_other_session_same_cwd_is_ignored(self):
        write_session(self.home, SID, BASE_ROWS)
        write_session(self.home, OTHER, [ctx("2026-10-17T00:01:00Z", "gpt-other"),
                                         tc("2026-10-17T00:11:00Z", usage(90000, 0, 9000))])
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: gpt-test · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k) · 비용 미산정")

    def test_no_session_id_means_no_record_even_with_same_cwd(self):
        write_session(self.home, SID, BASE_ROWS)
        os.environ.pop("CODEX_THREAD_ID")
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (지금 세션 번호를 알 수 없습니다)")

    def test_counter_reset(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                tc("2026-10-17T00:05:00Z", usage(1000, 0, 100)),
                tc("2026-10-17T00:12:00Z", usage(3000, 0, 300)),   # +2000/+200
                tc("2026-10-17T00:14:00Z", usage(500, 0, 50)),     # 초기화 → +500/+50
                tc("2026-10-17T00:16:00Z", usage(800, 0, 80))]     # +300/+30
        write_session(self.home, SID, rows)
        t = self.per()["gpt-test"]
        self.assertEqual((t["input_tokens"], t["output_tokens"]), (2800, 280))

    def test_missing_start_value_is_no_record(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                tc("2026-10-17T00:12:00Z", usage(3000, 0, 300))]   # 시작 전 누적값 없음
        write_session(self.home, SID, rows)
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (구간 시작 누적값이 없습니다)")

    def test_missing_start_value_uses_snapshot(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                tc("2026-10-17T00:12:00Z", usage(3000, 0, 300))]
        write_session(self.home, SID, rows)
        (self.proj / ".aml").mkdir()
        (self.proj / ".aml" / "codex-measure-start.json").write_text(json.dumps(
            {"label": "t", "session": SID, "since": SINCE, "usage": usage(1000, 0, 100)}))
        t = self.per()["gpt-test"]
        self.assertEqual((t["input_tokens"], t["output_tokens"]), (2000, 200))

    def test_snapshot_from_other_session_is_not_used(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                tc("2026-10-17T00:12:00Z", usage(3000, 0, 300))]
        write_session(self.home, SID, rows)
        (self.proj / ".aml").mkdir()
        (self.proj / ".aml" / "codex-measure-start.json").write_text(json.dumps(
            {"label": "t", "session": OTHER, "since": SINCE, "usage": usage(1000, 0, 100)}))
        self.assertIn("기록 없음", ob.task_done_line(SINCE, "t", end=END))

    def test_no_sessions_dir(self):
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (Codex 세션 기록 폴더가 없습니다)")

    def test_unknown_format(self):
        write_session(self.home, SID, BASE_ROWS, with_meta=False)
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (세션 기록의 형식을 알 수 없습니다)")

    def test_old_version_is_not_guessed(self):
        write_session(self.home, SID, BASE_ROWS, version="0.135.0")
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (확인하지 않은 Codex 버전의 기록입니다)")

    def test_inconsistent_numbers_are_not_guessed(self):
        # 0.135 시절처럼 추론이 출력보다 크고 캐시가 입력보다 큰 기록
        odd = {"input_tokens": 2521, "cached_input_tokens": 3968, "cache_write_input_tokens": 0,
               "output_tokens": 395, "reasoning_output_tokens": 13843, "total_tokens": 16759}
        rows = BASE_ROWS[:2] + [tc("2026-10-17T00:12:00Z", odd)]
        write_session(self.home, SID, rows)
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 기록 없음 (토큰 숫자의 관계가 예상과 다릅니다)")

    def test_no_usage_in_interval_is_not_zero_cost(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                tc("2026-10-17T00:05:00Z", usage(1000, 0, 100))]
        write_session(self.home, SID, rows)
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END), "측정: 10분 0초 · 토큰 기록 없음")

    def test_multi_model(self):
        rows = [ctx("2026-10-17T00:01:00Z", "gpt-a"),
                tc("2026-10-17T00:05:00Z", usage(1000, 0, 100)),
                tc("2026-10-17T00:12:00Z", usage(2000, 500, 200)),   # gpt-a +1000(캐시 500)/+100
                ctx("2026-10-17T00:13:00Z", "gpt-b"),
                tc("2026-10-17T00:14:00Z", usage(5000, 500, 500))]   # gpt-b +3000/+300
        write_session(self.home, SID, rows)
        self.assertEqual(ob.task_done_line(SINCE, "t", end=END),
                         "측정: 10분 0초 · gpt-a(입력 500/출력 100) + gpt-b(입력 3.0k/출력 300) · 비용 미산정")


class TestCost(unittest.TestCase):
    TOK = {"input_tokens": 3_000_000, "cached_input_tokens": 1_000_000,
           "cache_write_input_tokens": 0, "output_tokens": 500_000,
           "reasoning_output_tokens": 200_000, "total_tokens": 3_500_000}

    def test_known_price_counts_cache_once(self):
        # 캐시 안 된 입력 2M × $2 + 캐시 1M × $0.5 + 출력 0.5M × $8 (추론은 출력 안에 있음)
        c = ob.cost_usd("gpt-test", self.TOK, {"gpt-test": (2.0, 0.5, 8.0)})
        self.assertAlmostEqual(c, 4.0 + 0.5 + 4.0)

    def test_unknown_model_has_no_cost(self):
        self.assertIsNone(ob.cost_usd("gpt-unknown", self.TOK, {"gpt-test": (2.0, 0.5, 8.0)}))

    def test_cache_write_without_price_is_not_guessed(self):
        tok = dict(self.TOK, cache_write_input_tokens=10)
        self.assertIsNone(ob.cost_usd("gpt-test", tok, {"gpt-test": (2.0, 0.5, 8.0)}))

    def test_partial_cost_is_marked(self):
        per = {"gpt-test": self.TOK, "gpt-unknown": self.TOK}
        line = ob.measure_line(60, per, {"gpt-test": (2.0, 0.5, 8.0)})
        self.assertTrue(line.endswith("· 예상 비용 $8.50 (일부 비용 미산정)"), line)


class TestSummary(unittest.TestCase):
    PROGRESS = """# 진행 기록
- <observe.py 출력을 그대로 — `측정: …` 한 줄: 모델 · 걸린 시간 · 토큰 · 예상 비용. 실패하면 `측정: 기록 없음`>
- 측정: claude-opus-5-5 · 4분 16초 · 토큰 입력 74 / 출력 65k (캐시 읽기 5.9M / 쓰기 105k) · 예상 비용 $5.23
- 측정: gpt-test · 10분 0초 · 토큰 입력 2.4k / 출력 500 (캐시 읽기 1.6k) · 비용 미산정
- 측정: 1분 30초 · gpt-a(입력 500/출력 100) + gpt-b(입력 3.0k/출력 300) · 예상 비용 $0.50 (일부 비용 미산정)
- 측정: 기록 없음 (지금 세션 번호를 알 수 없습니다)
- 측정: 기록 없음
"""

    def test_mixed_claude_codex_lines(self):
        self.assertEqual(ob.summarize_progress(self.PROGRESS), "\n".join([
            "요약: 작업 5개 · 총 15분 46초 · 토큰 대략 입력 6.0k / 출력 65.9k · 알려진 비용 합계 $5.73",
            "모델: claude-opus-5-5 1회 · gpt-a 1회 · gpt-b 1회 · gpt-test 1회",
            "비용 미산정 작업: 2개 (가격을 확인하지 못한 모델 — 0 으로 치지 않음)",
            "측정 없는 작업: 2개"]))

    def test_empty(self):
        self.assertEqual(ob.summarize_progress("# 진행 기록\n"), "요약: 측정 줄이 아직 없습니다")


class TestCli(Base):
    def run_cli(self, *args):
        env = dict(os.environ)
        return subprocess.run([sys.executable, str(OBSERVE), *args], cwd=self.proj, env=env,
                              capture_output=True, text=True)

    def test_start_then_done_round_trip(self):
        write_session(self.home, SID, [ctx("2026-10-17T00:01:00Z", "gpt-test"),
                                       tc("2026-10-17T00:05:00Z", usage(1000, 0, 100))])
        r = self.run_cli("task-start", "--label", "1.1 시험")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("시작: "), r.stdout)
        self.assertTrue((self.proj / ".aml" / "codex-measure-start.json").exists())
        r = self.run_cli("task-done", "--since", r.stdout.split("시작: ")[1].strip(), "--label", "1.1 시험")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("측정: "), r.stdout)
        self.assertIn("토큰 기록 없음", r.stdout)        # 시작 뒤에 쓴 토큰이 없음 (0 비용으로 표시 안 함)
        self.assertFalse((self.proj / ".aml" / "codex-measure-start.json").exists())

    def test_bad_input_never_fails(self):
        os.environ.pop("CODEX_THREAD_ID")
        for args in (("task-done", "--since", "어제"), ("task-done", "--since", SINCE),
                     ("task-start",), ("check",), ("summary", "없는파일.md")):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, (args, r.stderr))
        self.assertIn("기록 없음", self.run_cli("task-done", "--since", SINCE).stdout)
        self.assertIn("기록 없음", self.run_cli("check").stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
