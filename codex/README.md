# automix-light — Codex 판

Codex 에서 쓰는 aml 입니다. Claude Code 판과 같은 흐름(기획 → 구현 → 검증 → 기록 → 다음 바퀴)을 Codex 스킬 7개로 씁니다. 모든 대화와 산출물은 한국어입니다.

## 설치

필요한 것: [Codex CLI](https://developers.openai.com/codex) 와 git. 측정 줄을 남기려면 `python3` 도 있으면 좋지만, 없어도 작업은 진행됩니다.

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
codex plugin marketplace add "$PWD/codex"
codex plugin add aml@automix-light
codex plugin list            # aml@automix-light  installed, enabled 가 보이면 됩니다
```

Codex 를 새로 열고 `$aml-` 을 입력했을 때 아래 스킬 7개가 보이면 설치가 끝난 것입니다. 마켓플레이스는 내려받은 폴더를 가리키니, 폴더를 지우거나 옮기지 마세요.

### 예전 Codex 판(0.2.0)이 깔려 있다면

예전 판도 이름이 `aml@automix-light` 라서 어느 쪽이 실행되는지 헷갈릴 수 있습니다. 새로 설치하기 전에 확인하고 지웁니다.

```bash
codex plugin list                              # VERSION 이 0.2.0... 이면 예전 판
codex plugin remove aml@automix-light          # 예전 판 지우기
codex plugin marketplace list                  # 예전 automix-light 마켓플레이스가 남아 있으면
codex plugin marketplace remove automix-light  #   지운 뒤 위의 설치를 다시 합니다
```

이 명령들은 `~/.codex/config.toml` 을 바꿉니다. 직접 실행할지 먼저 정하세요.

## 스킬

| 스킬 | 하는 일 | Claude Code 판 |
|---|---|---|
| `$aml-new` | 인터뷰로 `intent.md`·`spec.md`·`task.md`·`progress.md` 만들기 (구현은 안 함) | `/aml:new` |
| `$aml-go` | `task.md` 를 순서대로 구현·검증하고 기록, 할 일마다 커밋 | `/aml:go` |
| `$aml-review` | 커밋 전에 버그·안전·약속 지킴 점검 (코드는 안 고침) | `/aml:review` |
| `$aml-next` | 써 본 결과를 다음 할 일이나 새 기획으로 | `/aml:next` |
| `$aml-rule` | 두 번 반복된 실수를 `AGENTS.md` 나 규칙 카드(`.agents/skills/`)로 | `/aml:rule` |
| `$aml-status` | 진행 상황과 시간·토큰·비용 요약 | `/aml:status` |
| `$aml-doctor` | 시작 전 점검 (파일은 안 바꿈) | `/aml:doctor` |

프로젝트 안내 파일은 `CLAUDE.md` 대신 `AGENTS.md` 입니다. Codex 가 매 세션 자동으로 읽습니다.

## Claude Code 판과 다른 점 (꼭 읽어 주세요)

- **안전망** — 이 버전에는 AML 전용 차단 훅이 없습니다. Codex 의 권한·샌드박스·승인 설정은 환경에 따라 적용되며, Claude 판 AML 훅과 같은 차단을 보장하지 않습니다. Claude 판이 막아 주는 비밀키(.env) 커밋, 버그 고치는 중 테스트 파일 수정, 강제 푸시·하드 리셋은 Codex 판에서는 스킬의 안내로만 피합니다 — 실제로 실행되기 전에 사람이 확인하세요.
- **독립 확인** — 기본은 같은 세션 안의 **자체 확인**입니다. 별도 도우미에게 실제로 맡겼을 때만 `progress.md` 에 "독립 확인"이라고 적습니다.
- **사용량 측정** — Codex 세션 기록(`~/.codex/sessions/`)에서 이번 할 일 동안 쓴 토큰을 읽어 측정 줄을 남깁니다. 지금 세션을 확실히 찾지 못하거나 시작점 기록이 없으면 다른 세션 값으로 채우지 않고 `측정: 기록 없음` 을 남깁니다. 가격을 확인한 모델만 비용을 계산하고, 나머지는 "비용 미산정"으로 표시합니다. 자세한 기준은 [`aml/references/telemetry.md`](aml/references/telemetry.md).
- **Langfuse 전송** — Codex 판 첫 버전에는 없습니다.

## Claude Code 에서 하던 프로젝트를 Codex 로 옮길 때

새로 기획하지 않습니다. 계획·기록 파일은 그대로 쓰고, Codex 용 안내 파일 하나만 준비합니다.

1. 프로젝트 폴더에 `spec.md`·`task.md`·`progress.md` 가 있고, `CLAUDE.md` 의 "확인하는 법"에 실행·테스트 명령이 있는지 봅니다.
2. `AGENTS.md` 가 **없을 때만** Codex 에 이렇게 요청합니다: "spec.md·task.md·progress.md 는 그대로 두고, CLAUDE.md 의 내용(특히 확인하는 법)을 옮겨서 aml 의 AGENTS 템플릿 모양으로 AGENTS.md 만 만들어 줘. 다른 파일은 바꾸지 마."
3. `$aml-doctor` 로 점검합니다.
4. `$aml-go` 로 이어서 진행합니다.

`AGENTS.md` 가 이미 있으면 그대로 두고, `CLAUDE.md` 와 다른 점이 있으면 어느 쪽이 맞는지 정해서 직접 고칩니다. `REVIEW.md` 는 두 도구가 함께 씁니다. `.claude/skills/` 의 규칙 카드는 Codex 가 읽지 않으니, 계속 지킬 것만 `$aml-rule` 로 새로 적습니다. 한 번에 한 도구만 쓰고, 넘어가기 전에 커밋해 두세요. 자세한 내용: [`aml/references/switching.md`](aml/references/switching.md)

반대 방향(Codex → Claude Code)은 [Claude Code 판 안내](../claude-code/README.md#codex-에서-하던-프로젝트를-claude-code-로-옮길-때)를 보세요.

## 테스트 (이 저장소를 고치는 사람용)

```bash
bash codex/tests/test-templates.sh   # 공통 템플릿 5개가 두 판에서 똑같은지
```
