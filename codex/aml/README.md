# aml — Codex 판 패키지

초보자를 위한 한국어 기획 → 구현 → 검증 → 기록 흐름입니다. 설치 방법과 Claude Code 판과의 차이는 저장소의 `codex/README.md` 에 있습니다.

## 스킬

| 스킬 | 하는 일 |
|---|---|
| `aml-new` | 인터뷰로 `intent.md`·`spec.md`·`task.md`·`progress.md` 만들기 (구현은 안 함) |
| `aml-go` | `task.md` 를 순서대로 구현·검증하고 `progress.md` 에 기록 |
| `aml-review` | 커밋 전 버그·안전·약속 지킴 점검 (코드는 안 고침) |
| `aml-next` | 써 본 결과를 다음 할 일이나 새 기획으로 |
| `aml-rule` | 두 번 반복된 실수를 `AGENTS.md` 나 규칙 카드(`.agents/skills/`)로 |
| `aml-status` | 진행 상황과 시간·토큰·비용 요약 |
| `aml-doctor` | 시작 전 점검 (파일은 안 바꿈) |

## 폴더

- `skills/` — 스킬 7개
- `templates/` — 공통 템플릿 5개(spec · task · progress · intent · review, Claude Code 판과 같은 내용)와 Codex 전용 `agents.template.md` · `skill.template.md`
- `references/` — [도구 전환 준비](references/switching.md) · [완성 기준 확인](references/verification.md) · [측정 기준](references/telemetry.md) · [단계별 문서의 역할](references/artifact-chain.md)
- `scripts/observe.py` — 측정 줄 만들기와 요약 (파이썬 표준 라이브러리만 사용)

## 안전망

이 버전에는 AML 전용 차단 훅이 없습니다. Codex 의 권한·샌드박스·승인 설정은 환경에 따라 적용되며, Claude 판 AML 훅과 같은 차단을 보장하지 않습니다.
