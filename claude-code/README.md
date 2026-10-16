# automix-light — Claude Code 판

Claude Code 에서 쓰는 aml 입니다. 명령 7개(`/aml:new` · `/aml:go` · `/aml:review` · `/aml:next` · `/aml:rule` · `/aml:status` · `/aml:doctor`)로 기획 → 구현 → 검증 → 기록 → 다음 바퀴를 진행합니다. 명령별 자세한 설명은 [`aml/README.md`](aml/README.md) 에 있습니다.

## 설치

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
bash claude-code/install.sh   # ~/.claude-marketplaces/automix-light에 복사합니다
```

그런 다음 Claude Code 에서:

```text
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

`/help` 에 `/aml:` 명령 7개가 보이면 설치가 끝난 것입니다. 예전 설치 명령(`./install.sh`)은 이제 `bash claude-code/install.sh` 입니다.

## 테스트

```bash
bash claude-code/tests/e2e-smoke-guard.sh     # 위험한 작업 차단: 6가지 사례
bash claude-code/tests/e2e-smoke-observe.sh   # 측정 줄 기록과 설치 결과
```

## Codex 에서 하던 프로젝트를 Claude Code 로 옮길 때

새로 기획하지 않습니다. `intent.md`·`spec.md`·`task.md`·`progress.md`·`REVIEW.md` 는 두 도구에서 같은 모양이라 그대로 이어서 씁니다. 다른 것은 프로젝트 안내 파일(Codex 는 `AGENTS.md`, Claude Code 는 `CLAUDE.md`)과 규칙 카드 위치(`.agents/skills/` ↔ `.claude/skills/`)뿐입니다.

1. 프로젝트 폴더에 `spec.md`·`task.md`·`progress.md` 가 있고, `AGENTS.md` 의 "확인하는 법"에 실행·테스트 명령이 있는지 봅니다.
2. `CLAUDE.md` 가 **없을 때만** Claude Code 에 이렇게 요청합니다: "spec.md·task.md·progress.md 는 그대로 두고, AGENTS.md 의 내용(특히 확인하는 법)을 옮겨서 aml 의 CLAUDE 템플릿 모양으로 CLAUDE.md 만 만들어 줘. 다른 파일은 바꾸지 마."
3. `/aml:doctor` 로 점검합니다.
4. `/aml:go` 로 이어서 진행합니다. 체크된 할 일과 지난 기록은 그대로 둡니다.

하지 않는 것:

- `/aml:new` 로 처음부터 다시 시작하지 않습니다 — 체크 상태와 기록이 사라집니다.
- `CLAUDE.md` 가 이미 있으면 덮어쓰지 않습니다. `AGENTS.md` 와 실행·테스트 명령이 다르면 어느 쪽이 맞는지 정해서 직접 고칩니다.
- `REVIEW.md` 는 두 도구가 함께 씁니다. 새로 만들지 않습니다.
- `.agents/skills/` 의 규칙 카드는 Claude Code 가 읽지 않습니다. 계속 지킬 것만 `/aml:rule` 로 새로 적습니다.
- 두 도구를 동시에 쓰지 않습니다. 넘어가기 전에 커밋해 두세요.

Claude Code 판에는 되돌리기 어려운 일을 막는 AML 훅(`aml/hooks/aml-guard.sh`)이 있습니다. Codex 판에는 이 훅이 없습니다 — 반대 방향(Claude Code → Codex)으로 옮길 때는 [Codex 판 안내](../codex/README.md#claude-code-에서-하던-프로젝트를-codex-로-옮길-때)를 보세요.
