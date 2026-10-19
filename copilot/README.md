# automix-light — Copilot CLI 판

GitHub Copilot CLI(터미널에서 쓰는 `copilot`)에서 사용하는 aml입니다. 스킬 7개로 Claude Code 판과 같은 작업 흐름(기획 → 구현 → 검증 → 기록 → 사용 후 개선)을 진행합니다. 모든 대화와 문서는 한국어로 작성합니다.

> Copilot CLI **1.0.98**에서 설치·스킬 목록·안전망 훅·사용량 기록을 확인했습니다(2026-10-19). VS Code의 Copilot Chat은 지원 대상이 아닙니다 — 같은 플러그인을 읽을 수도 있지만 확인하지 않았습니다.

## 설치

[GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli)(Copilot 구독 필요)와 Git이 필요합니다. 작업 지표를 기록하고 안전망 훅을 쓰려면 `python3`도 필요합니다. 없어도 작업은 진행되지만, 그때는 측정이 `기록 없음`으로 남고 훅은 아무것도 막지 않습니다.

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
copilot plugin marketplace add "$PWD/copilot"
copilot plugin install aml@automix-light
copilot plugin list            # aml@automix-light (v0.6.0) (enabled) 인지 확인합니다
```

**`copilot/` 폴더를 등록하세요.** Copilot은 Claude Code용 마켓플레이스 파일도 읽기 때문에, 실수로 `claude-code/` 폴더를 등록하면 Claude Code 판이 설치되어 헷갈립니다. 마켓플레이스는 내려받은 폴더를 직접 읽으므로 그 폴더를 지우거나 옮기지 마세요.

Copilot을 새로 열고 `/aml`을 입력했을 때 `/aml:go`처럼 플러그인 이름이 앞에 붙은 스킬 7개가 보이면 설치가 끝난 것입니다. 스킬은 `/aml:go`처럼 입력하거나 "남은 할 일 진행해 줘"처럼 말로 요청해도 됩니다. Copilot에는 `/new`(새 대화)·`/review`(코드 리뷰) 같은 기본 명령이 따로 있으니, aml 스킬은 꼭 `/aml:new`처럼 `aml:`을 붙여 부르세요.

설치가 잘 됐는지 더 보려면 Copilot 대화에서 `/env`를 입력합니다. **Custom Agents**에 `verifier`, **Hooks**에 `preToolUse: 1 hook (sources: aml)`이 보이면 확인 도우미와 안전망이 켜진 것입니다.

## 스킬

| 스킬 | 하는 일 | Claude Code 판 | Codex 판 |
|---|---|---|---|
| `/aml:new` | 질문과 답변으로 `intent.md`·`spec.md`·`task.md`·`progress.md` 작성 (구현은 하지 않음) | `/aml:new` | `$aml:new` |
| `/aml:go` | `task.md`의 작업을 순서대로 구현·검증하고 결과를 기록한 뒤 작업별로 커밋 | `/aml:go` | `$aml:go` |
| `/aml:review` | 커밋 전에 버그, 보안 문제, 요구사항 충족 여부 점검 (코드는 수정하지 않음) | `/aml:review` | `$aml:review` |
| `/aml:next` | 사용 중 발견한 문제와 필요한 기능을 다음 작업이나 새 기획으로 정리 | `/aml:next` | `$aml:next` |
| `/aml:rule` | 같은 실수가 두 번 반복되면 예방 규칙을 `AGENTS.md`나 규칙 카드(`.agents/skills/`)에 작성 | `/aml:rule` | `$aml:rule` |
| `/aml:status` | 진행 상황과 시간·토큰·AI 크레딧 요약 | `/aml:status` | `$aml:status` |
| `/aml:doctor` | 작업 시작 전 준비 상태 점검 (파일은 수정하지 않음) | `/aml:doctor` | `$aml:doctor` |

프로젝트 안내 파일은 `AGENTS.md`입니다(Codex 판과 같은 파일). Copilot은 매 세션 `AGENTS.md`와 `CLAUDE.md`를 함께 읽습니다.

## 알아 둘 점

- **위험한 작업 차단** — Claude Code 판처럼 aml 안전망 훅이 `.env` 커밋, 버그 수정 중 테스트 파일 변경, 강제 푸시·하드 리셋·통째로 지우기를 막고, 막은 이유와 해결 방법을 화면에 보여 줍니다. 다만 Copilot은 훅이 시간(10초)을 넘기면 막지 않고 그냥 통과시킵니다. 되돌리기 어려운 일은 사람도 한 번 더 봐 주세요. 끄려면 프로젝트의 `.aml/config.yaml`에 `guard: "off"`를 적습니다.
- **독립 확인** — `/aml:go`가 끝날 때 확인 도우미(`verifier` 에이전트)를 불러 새 눈으로 완성 기준을 확인합니다. 실제로 불렀을 때만 `progress.md`에 "독립 확인"이라고 적고, 부르지 못하면 "자체 확인"이라고 적습니다.
- **사용량 측정** — Copilot 세션 기록(`~/.copilot/session-state/`)에서 현재 작업에 쓴 토큰과 AI 크레딧을 읽습니다. Copilot이 직접 기록한 숫자라 화면 끝에 나오는 `Tokens`·`AI Credits`와 같습니다. 현재 세션을 확실히 찾지 못하거나 작업 도중 세션이 바뀌었으면 `측정: 기록 없음`으로 표시하고, 다른 세션의 값으로 채우지 않습니다. 달러 비용은 단가를 확인한 모델만 계산하고, 나머지는 "비용 미산정"으로 표시합니다. 자세한 기준은 [작업 지표 측정 기준](aml/references/telemetry.md)을 참고하세요.
- **Langfuse 전송** — Copilot 판 첫 버전에서는 지원하지 않습니다.

## 다른 도구에서 진행하던 프로젝트를 옮길 때

계획·기록 파일은 세 판이 같은 모양이라 새로 기획할 필요가 없습니다.

| 어디서 → 어디로 | 할 일 |
|---|---|
| Codex → Copilot | 없음. 같은 `AGENTS.md`와 `.agents/skills/`를 씁니다. 바로 `/aml:go` |
| Claude Code → Copilot | `AGENTS.md`만 만듭니다(아래 순서). `.claude/skills/`의 규칙 카드는 Copilot도 읽으니 옮기지 않습니다 |
| Copilot → Codex | 없음. 바로 `$aml:go` |
| Copilot → Claude Code | `CLAUDE.md`만 만듭니다. [Claude Code 판 안내](../claude-code/README.md#codex에서-진행하던-프로젝트를-claude-code로-옮길-때)의 순서가 그대로 맞습니다 |

Claude Code에서 진행하던 프로젝트를 Copilot으로 옮길 때:

1. 프로젝트 폴더에 `spec.md`·`task.md`·`progress.md`가 있고, `CLAUDE.md`의 "확인하는 법"에 실행·테스트 명령이 있는지 확인합니다.
2. `AGENTS.md`가 **없을 때만** Copilot에 이렇게 요청합니다: "spec.md·task.md·progress.md는 그대로 두고, CLAUDE.md의 내용(특히 확인하는 법)을 옮겨서 aml의 AGENTS 템플릿 형식에 맞춰 AGENTS.md만 만들어 줘. 다른 파일은 바꾸지 마."
3. `/aml:doctor`로 점검합니다.
4. `/aml:go`로 이어서 진행합니다.

`AGENTS.md`가 이미 있으면 그대로 두고, `CLAUDE.md`와 다른 점이 있으면 어느 쪽이 맞는지 확인해 직접 고칩니다. Copilot은 두 파일을 함께 읽기 때문에 내용이 다르면 헷갈립니다. `REVIEW.md`는 세 도구가 함께 씁니다. 한 번에 한 도구만 사용하고, 전환하기 전에 커밋해 두세요. 자세한 내용은 [도구 전환 안내](aml/references/switching.md)를 참고하세요.

## 테스트 (저장소 수정 시)

```bash
bash copilot/tests/test-templates.sh   # 세 판의 공통 템플릿 5개 일치 여부 확인
bash copilot/tests/test-guard.sh       # 안전망 훅: 막을 것·통과시킬 것 (Copilot 입력 모양)
python3 copilot/tests/test_observe.py  # 측정·요약 숫자 검사
bash copilot/tests/test-package.sh     # 패키지 구조 (copilot 명령이 있으면 격리 설치와 스킬 목록까지)
```
