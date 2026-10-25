# aml — Copilot CLI 판 패키지

처음 앱을 만드는 사람이 한국어로 기획부터 구현, 검증, 기록까지 진행하도록 돕는 플러그인입니다. 설치 방법이나 다른 도구용 버전과 다른 점은 저장소의 `copilot/README.md`를 참고하세요.

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

Copilot에는 `/new`·`/review` 같은 기본 명령이 있으므로, aml 스킬을 실행할 때는 꼭 `aml:`을 붙여 입력합니다.

## 폴더

- `plugin.json` — 플러그인 설정 (스킬·에이전트·훅 위치)
- `skills/` — 스킬 7개
- `agents/verifier.agent.md` — 독립 검증을 담당하는 에이전트 (`/aml:go`가 끝날 때 호출)
- `hooks.json` · `hooks/aml-guard.sh` — 안전망 훅 (되돌리기 어려운 세 종류의 작업을 차단)
- `templates/` — 공통 템플릿 5개(spec · task · progress · intent · review, 다른 판과 같은 내용)와 Copilot 전용 `agents.template.md` · `skill.template.md`
- `references/` — [도구 전환 준비](references/switching.md) · [완성 기준 확인](references/verification.md) · [측정 기준](references/telemetry.md) · [단계별 문서의 역할](references/artifact-chain.md)
- `scripts/observe.py` — 작업 지표를 기록하고 요약하는 스크립트 (파이썬 표준 라이브러리만 사용)

## 위험한 작업 차단

aml 안전망 훅은 `.env` 커밋, 버그 수정 중(`.aml/FIXING`) 테스트 파일 변경, 강제 푸시·하드 리셋·대량 파일 삭제를 막습니다. `spec.md`와 `task.md`가 있는 aml 프로젝트에서만 동작합니다. 훅에서 오류가 발생하거나 실행 시간이 제한을 넘으면 작업이 차단되지 않으므로, 되돌리기 어려운 작업은 직접 한 번 더 확인하세요.
