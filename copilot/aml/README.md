# aml — Copilot CLI 판 패키지

초보자가 한국어로 기획 → 구현 → 검증 → 기록 과정을 진행할 수 있도록 돕는 플러그인입니다. 설치 방법과 다른 판과의 차이는 저장소의 `copilot/README.md`에 있습니다.

## 스킬

| 스킬 | 하는 일 |
|---|---|
| `/aml:new` | 질문과 답변으로 `intent.md`·`spec.md`·`task.md`·`progress.md` 작성 (구현은 하지 않음) |
| `/aml:go` | `task.md`의 작업을 순서대로 구현·검증하고 결과를 `progress.md`에 기록 |
| `/aml:review` | 커밋 전에 버그, 보안 문제, 요구사항 충족 여부 점검 (코드는 수정하지 않음) |
| `/aml:next` | 사용 중 발견한 문제와 필요한 기능을 다음 작업이나 새 기획으로 정리 |
| `/aml:rule` | 같은 실수가 두 번 반복되면 예방 규칙을 `AGENTS.md`나 규칙 카드(`.agents/skills/`)에 작성 |
| `/aml:status` | 진행 상황과 시간·토큰·AI 크레딧 요약 |
| `/aml:doctor` | 작업 시작 전 준비 상태 점검 (파일은 수정하지 않음) |

Copilot에는 `/new`·`/review` 같은 기본 명령이 있으니, aml 스킬은 꼭 `aml:`을 붙여 부릅니다.

## 폴더

- `plugin.json` — 플러그인 설정 (스킬·에이전트·훅 위치)
- `skills/` — 스킬 7개
- `agents/verifier.agent.md` — 독립 확인 도우미 (`/aml:go`가 끝날 때 부름)
- `hooks.json` · `hooks/aml-guard.sh` — 안전망 훅 (되돌리기 어려운 일 세 가지를 막음)
- `templates/` — 공통 템플릿 5개(spec · task · progress · intent · review, 다른 판과 같은 내용)와 Copilot 전용 `agents.template.md` · `skill.template.md`
- `references/` — [도구 전환 준비](references/switching.md) · [완성 기준 확인](references/verification.md) · [측정 기준](references/telemetry.md) · [단계별 문서의 역할](references/artifact-chain.md)
- `scripts/observe.py` — 작업 지표 기록 및 요약 (파이썬 표준 라이브러리만 사용)

## 위험한 작업 차단

aml 안전망 훅이 `.env` 커밋, 버그 수정 중(`.aml/FIXING`) 테스트 파일 변경, 강제 푸시·하드 리셋·통째로 지우기를 막습니다. spec.md와 task.md가 있는 aml 프로젝트에서만 동작하고, 훅 안에서 문제가 생기면 막지 않고 통과시킵니다. Copilot은 훅이 시간을 넘기면 막지 않고 통과시키니, 되돌리기 어려운 일은 사람도 한 번 더 확인하세요.
