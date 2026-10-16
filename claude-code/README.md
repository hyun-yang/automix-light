# automix-light — Claude Code 판

Claude Code에서 사용하는 aml입니다. 명령어 7개(`/aml:new` · `/aml:go` · `/aml:review` · `/aml:next` · `/aml:rule` · `/aml:status` · `/aml:doctor`)로 기획 → 구현 → 검증 → 기록 → 사용 후 개선 과정을 진행합니다. 명령어별 자세한 설명은 [`aml/README.md`](aml/README.md)에 있습니다.

## 설치

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
bash claude-code/install.sh   # ~/.claude-marketplaces/automix-light에 복사합니다
```

그런 다음 Claude Code에서 다음 명령을 입력합니다.

```text
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

`/help`에 `/aml:` 명령어 7개가 표시되면 설치가 완료된 것입니다. 예전 설치 명령(`./install.sh`)은 `bash claude-code/install.sh`로 바뀌었습니다.

## 테스트

```bash
bash claude-code/tests/e2e-smoke-guard.sh     # 위험한 작업 차단: 6가지 사례
bash claude-code/tests/e2e-smoke-observe.sh   # 작업 지표 기록 및 설치 결과 확인
```

## Codex에서 진행하던 프로젝트를 Claude Code로 옮길 때

`intent.md`·`spec.md`·`task.md`·`progress.md`·`REVIEW.md`는 두 도구에서 형식이 같아 그대로 사용할 수 있습니다. 프로젝트 안내 파일(Codex는 `AGENTS.md`, Claude Code는 `CLAUDE.md`)과 규칙 카드 위치(`.agents/skills/` ↔ `.claude/skills/`)만 다릅니다.

1. 프로젝트 폴더에 `spec.md`·`task.md`·`progress.md`가 있고, `AGENTS.md`의 "확인하는 법"에 실행·테스트 명령이 있는지 확인합니다.
2. `CLAUDE.md`가 **없을 때만** Claude Code에 이렇게 요청합니다: "spec.md·task.md·progress.md는 그대로 두고, AGENTS.md의 내용(특히 확인하는 법)을 옮겨서 aml의 CLAUDE 템플릿 형식에 맞춰 CLAUDE.md만 만들어 줘. 다른 파일은 바꾸지 마."
3. `/aml:doctor`로 점검합니다.
4. `/aml:go`로 이어서 진행합니다. 작업의 완료 표시와 기존 기록은 그대로 둡니다.

전환 시 주의사항:

- `/aml:new`로 처음부터 다시 시작하지 않습니다. 작업의 완료 표시와 기록이 사라집니다.
- `CLAUDE.md`가 이미 있으면 덮어쓰지 않습니다. `AGENTS.md`와 실행·테스트 명령이 다르면 어느 쪽이 맞는지 확인해 직접 수정합니다.
- `REVIEW.md`는 두 도구에서 함께 사용하므로 새로 만들지 않습니다.
- `.agents/skills/`의 규칙 카드는 Claude Code가 읽지 않습니다. 계속 적용할 규칙만 `/aml:rule`로 다시 작성합니다.
- 두 도구를 동시에 사용하지 않습니다. 전환하기 전에 커밋해 두세요.

Claude Code 판에는 되돌리기 어려운 작업을 차단하는 AML 훅(`aml/hooks/aml-guard.sh`)이 있습니다. Codex 판에는 이 훅이 없습니다. 반대 방향(Claude Code → Codex)으로 옮길 때는 [Codex 판 안내](../codex/README.md#claude-code에서-진행하던-프로젝트를-codex로-옮길-때)를 보세요.
