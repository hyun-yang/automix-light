# 도구 전환 준비 — Claude Code · Codex ↔ Copilot CLI

aml 의 계획·기록 파일(`intent.md`·`spec.md`·`task.md`·`progress.md`·`REVIEW.md`)은 세 도구에서 같은 모양이라, 하던 프로젝트를 다른 도구로 옮겨도 **새로 기획할 필요가 없습니다.** 도구마다 다른 것은 두 가지뿐입니다.

| | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| 프로젝트 안내 파일 (매 세션 자동으로 읽음) | `CLAUDE.md` | `AGENTS.md` | `AGENTS.md` (`CLAUDE.md` 도 함께 읽음) |
| aml 이 규칙 카드를 만드는 곳 | `.claude/skills/` | `.agents/skills/` | `.agents/skills/` (`.claude/skills/`·`.github/skills/` 의 카드도 읽음) |
| 부르는 법 | `/aml:go` | `$aml:go` | `/aml:go` |

그래서 옮겨 갈 도구의 안내 파일이 **없을 때만** 그 파일 하나를 만들면 됩니다.

## 방향별로

| 어디서 → 어디로 | 할 일 |
|---|---|
| Codex → Copilot | 없음. 같은 `AGENTS.md` 와 `.agents/skills/` 를 씁니다. 바로 `/aml:go` |
| Claude Code → Copilot | `AGENTS.md` 만 만듭니다(아래 절차). 규칙 카드(`.claude/skills/`)는 Copilot 도 읽으니 옮기지 않습니다 |
| Copilot → Codex | 없음. 바로 `$aml:go` |
| Copilot → Claude Code | `CLAUDE.md` 만 만듭니다(아래 절차). Copilot 에서 만든 규칙 카드(`.agents/skills/`)는 Claude Code 가 읽지 않으니, 계속 지킬 것만 Claude Code 의 `/aml:rule` 로 새로 적습니다 |

## 절차 (안내 파일이 없을 때)

1. **지금 상태를 확인합니다.** `spec.md`·`task.md`·`progress.md` 가 있는지, 원래 도구의 안내 파일(`CLAUDE.md` 또는 `AGENTS.md`)의 "확인하는 법"에 실행·테스트 명령이 적혀 있는지 봅니다.
2. **옮겨 갈 도구에 없는 안내 파일만 만들어 달라고 요청합니다.** 옮겨 갈 도구에서 이렇게 말하면 됩니다.
   - Copilot 으로 옮길 때: "spec.md·task.md·progress.md 는 그대로 두고, CLAUDE.md 의 내용(특히 확인하는 법)을 옮겨서 aml 의 AGENTS 템플릿 모양으로 AGENTS.md 만 만들어 줘. 다른 파일은 바꾸지 마."
   - Claude Code 로 옮길 때: "spec.md·task.md·progress.md 는 그대로 두고, AGENTS.md 의 내용(특히 확인하는 법)을 옮겨서 aml 의 CLAUDE 템플릿 모양으로 CLAUDE.md 만 만들어 줘. 다른 파일은 바꾸지 마."
3. **점검합니다.** Copilot 은 `/aml:doctor`, Claude Code 도 `/aml:doctor`. 안내 파일이 있다고 나오고, 할 일이 남아 있으면 준비가 끝난 것입니다.
4. **이어서 진행합니다.** `/aml:go`. 체크된 할 일과 지난 기록은 그대로 두고, 체크 안 된 할 일부터 이어 갑니다.

## 하지 않는 것

- **새로 기획하지 않습니다.** 옮긴 뒤에 `/aml:new` 로 처음부터 다시 시작하거나 `spec.md`·`task.md` 를 새로 쓰지 않습니다. 체크 상태와 기록이 사라집니다.
- **이미 있는 안내 파일을 덮어쓰지 않습니다.** 옮겨 갈 도구의 안내 파일이 이미 있으면 그대로 둡니다. `CLAUDE.md` 와 `AGENTS.md` 의 내용(특히 실행·테스트 명령)이 서로 다르면 고치지 말고 다른 점을 사용자에게 알려 어느 쪽이 맞는지 묻습니다. Copilot 은 둘을 함께 읽기 때문에, 서로 다르면 헷갈립니다.
- **`REVIEW.md` 는 그대로 씁니다.** 세 도구가 같은 파일을 읽습니다. 새로 만들거나 덮어쓰지 않습니다.
- **여러 도구를 동시에 쓰지 않습니다.** 한 도구에서 할 일을 끝내고(커밋까지) 다른 도구로 넘어갑니다. 두 도구가 동시에 `task.md` 를 고치면 한쪽 내용이 덮어써질 수 있습니다.

## 알아 둘 차이

- **안전망**: Claude Code 판과 Copilot 판에는 되돌리기 어려운 일(비밀키 커밋, 고치는 중 테스트 파일 수정, 강제 푸시·하드 리셋)을 막는 aml 훅이 있습니다. Copilot 은 훅이 시간을 넘기면 막지 않고 통과시킵니다. Codex 판에는 aml 전용 차단 훅이 없습니다.
- **독립 확인**: Claude Code 판과 Copilot 판은 마지막에 별도 확인 도우미(verifier)를 부릅니다. Copilot 판은 실제로 불렀을 때만 "독립 확인"이라고 적고, 못 부르면 "자체 확인"이라고 적습니다.
- **측정 줄**: 세 도구의 측정 줄이 `progress.md` 에 섞여도 진행 요약(`/aml:status`)이 함께 합산합니다. Copilot 에서 사용량을 확실히 읽지 못하면 `측정: 기록 없음` 이 남습니다.
