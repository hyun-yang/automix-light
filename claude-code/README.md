# automix-light — Claude Code 판

Claude Code용 aml 플러그인입니다. 명령어 7개(`/aml:new` · `/aml:go` · `/aml:review` · `/aml:next` · `/aml:rule` · `/aml:status` · `/aml:doctor`)로 기획부터 구현, 검증, 기록, 사용 후 개선까지 진행할 수 있습니다. 각 명령어는 [`aml/README.md`](aml/README.md)에서 자세히 설명합니다.

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

**Windows 11**에서는 터미널(PowerShell)에서 `bash claude-code/install.sh` 대신 다음 명령을 실행하세요. Claude Code에는 `~/.claude-marketplaces/...` 대신 설치 명령 끝에 출력되는 `C:/Users/<사용자 이름>/.claude-marketplaces/automix-light` 경로를 그대로 붙여 넣으세요.

```powershell
powershell -ExecutionPolicy Bypass -File claude-code\install.ps1
```

`-ExecutionPolicy Bypass`는 이번 한 번의 실행에만 스크립트를 허용한다는 뜻으로, 컴퓨터의 보안 설정은 바뀌지 않습니다. 준비물(Git for Windows, Python)은 [루트 README의 "Windows 11에서 설치하기"](../README.md#windows-11에서-설치하기)를 참고하세요.

Windows의 작업 지표 측정과 doctor 점검은 실제로 실행되는 Python 3을 사용합니다. `python3`가 Microsoft Store 바로가기라면 `python`, 이어서 `py -3`를 확인합니다. [확인 방법](../README.md#windows-11에서-설치하기)을 참고하세요.

`/help`에 `/aml:` 명령어 7개가 표시되면 설치가 완료된 것입니다. 예전 설치 명령(`./install.sh`)은 `bash claude-code/install.sh`로 바뀌었습니다.

## 테스트

```bash
bash claude-code/tests/e2e-smoke-guard.sh     # 위험한 작업 차단: 6가지 사례
bash claude-code/tests/e2e-smoke-observe.sh   # 작업 지표 기록 및 설치 결과 확인
```

이 테스트는 저장소를 수정하는 사람을 위한 것으로, bash에서 실행합니다. Windows에서는 Git for Windows에 포함된 **Git Bash**를 사용하세요. 플러그인 설치만 한다면 테스트는 필요하지 않습니다. 자세한 주의사항은 [루트 README의 "테스트"](../README.md#테스트)를 참고하세요.

## Codex에서 진행하던 프로젝트를 Claude Code로 옮길 때

`intent.md`·`spec.md`·`task.md`·`progress.md`·`REVIEW.md`는 두 도구에서 형식이 같아 그대로 사용할 수 있습니다. 프로젝트 안내 파일(Codex는 `AGENTS.md`, Claude Code는 `CLAUDE.md`)과 규칙 카드 위치(`.agents/skills/` ↔ `.claude/skills/`)는 도구에 따라 다릅니다.

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
