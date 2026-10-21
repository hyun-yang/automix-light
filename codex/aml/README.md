# aml — Codex 판 패키지

처음 앱을 만드는 사람이 한국어로 기획부터 구현, 검증, 기록까지 진행하도록 돕는 플러그인입니다. 설치 방법과 Claude Code 판과의 차이를 알아보려면 저장소의 `codex/README.md`를 참고하세요.

## 스킬

| 스킬 | 하는 일 |
|---|---|
| `$aml:new` | 질문과 답변으로 `intent.md`·`spec.md`·`task.md`·`progress.md` 작성 (구현은 하지 않음) |
| `$aml:go` | `task.md`의 작업을 순서대로 구현·검증하고 결과를 `progress.md`에 기록 |
| `$aml:review` | 커밋 전에 버그, 보안 문제, 요구사항 충족 여부 점검 (코드는 수정하지 않음) |
| `$aml:next` | 사용 중 발견한 문제와 필요한 기능을 다음 작업이나 새 기획으로 정리 |
| `$aml:rule` | 같은 실수가 두 번 반복되면 예방 규칙을 `AGENTS.md`나 규칙 카드(`.agents/skills/`)에 작성 |
| `$aml:status` | 진행 상황과 시간·토큰·비용 요약 |
| `$aml:doctor` | 작업 시작 전 준비 상태 점검 (파일은 수정하지 않음) |

## 폴더

- `skills/` — 스킬 7개
- `templates/` — 공통 템플릿 5개(spec · task · progress · intent · review, Claude Code 판과 같은 내용)와 Codex 전용 `agents.template.md` · `skill.template.md`
- `references/` — [도구 전환 준비](references/switching.md) · [완성 기준 확인](references/verification.md) · [측정 기준](references/telemetry.md) · [단계별 문서의 역할](references/artifact-chain.md)
- `scripts/observe.py` — 작업 지표를 기록하고 요약하는 스크립트 (파이썬 표준 라이브러리만 사용)

## 위험한 작업 차단

이 버전에는 AML 전용 차단 훅이 없습니다. Codex의 권한·샌드박스·승인 설정은 환경에 따라 적용되며, Claude Code 판의 AML 훅과 동일한 차단을 보장하지 않습니다.
