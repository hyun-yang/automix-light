# automix-light — Codex 판

Codex에서 사용하는 aml입니다. 스킬 7개로 Claude Code 판과 같은 작업 흐름(기획 → 구현 → 검증 → 기록 → 사용 후 개선)을 진행합니다. 모든 대화와 문서는 한국어로 작성합니다.

## 설치

[Codex CLI](https://developers.openai.com/codex)와 Git이 필요합니다. 작업 지표를 기록하려면 `python3`도 필요하지만, 없어도 작업은 진행할 수 있습니다.

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
codex plugin marketplace add "$PWD/codex"
codex plugin add aml@automix-light
codex plugin list            # aml@automix-light의 상태가 installed, enabled인지 확인합니다
```

Codex를 새로 열고 `$aml`을 입력했을 때 `aml:new`처럼 플러그인 이름이 앞에 붙은 스킬 7개가 표시되면 설치가 완료된 것입니다. 스킬은 `$aml:go`처럼 입력하거나, "남은 할 일 진행해 줘"처럼 말로 요청해도 됩니다. Codex에는 `/new`·`/status`·`/review` 같은 기본 명령이 따로 있으므로, aml 스킬을 실행할 때는 `$aml:status`처럼 `$`를 사용하세요. 마켓플레이스가 내려받은 폴더를 참조하므로 해당 폴더를 삭제하거나 옮기지 마세요.

### 이전 Codex 판(0.2.0)이 설치되어 있다면

이전 판도 이름이 `aml@automix-light`여서 어느 버전이 실행되는지 혼동할 수 있습니다. 새로 설치하기 전에 설치된 버전을 확인하고 이전 판을 제거합니다.

```bash
codex plugin list                              # VERSION이 0.2.0...이면 이전 판
codex plugin remove aml@automix-light          # 이전 판 제거
codex plugin marketplace list                  # 기존 automix-light 마켓플레이스 확인
codex plugin marketplace remove automix-light  # 기존 항목이 남아 있으면 제거한 뒤 위의 설치 절차 진행
```

위 명령을 실행하면 `~/.codex/config.toml`이 변경되므로, 기존 설정을 확인한 뒤 실행하세요.

## 스킬

| 스킬 | 하는 일 | Claude Code 판 |
|---|---|---|
| `$aml:new` | 질문과 답변으로 `intent.md`·`spec.md`·`task.md`·`progress.md` 작성 (구현은 하지 않음) | `/aml:new` |
| `$aml:go` | `task.md`의 작업을 순서대로 구현·검증하고 결과를 기록한 뒤 작업별로 커밋 | `/aml:go` |
| `$aml:review` | 커밋 전에 버그, 보안 문제, 요구사항 충족 여부 점검 (코드는 수정하지 않음) | `/aml:review` |
| `$aml:next` | 사용 중 발견한 문제와 필요한 기능을 다음 작업이나 새 기획으로 정리 | `/aml:next` |
| `$aml:rule` | 같은 실수가 두 번 반복되면 예방 규칙을 `AGENTS.md`나 규칙 카드(`.agents/skills/`)에 작성 | `/aml:rule` |
| `$aml:status` | 진행 상황과 시간·토큰·비용 요약 | `/aml:status` |
| `$aml:doctor` | 작업 시작 전 준비 상태 점검 (파일은 수정하지 않음) | `/aml:doctor` |

프로젝트 안내 파일은 `AGENTS.md`입니다. Codex가 매 세션 자동으로 읽습니다.

## Claude Code 판과 다른 점 (꼭 읽어 주세요)

- **위험한 작업 차단** — 이 버전에는 AML 전용 차단 훅이 없습니다. Codex의 권한·샌드박스·승인 설정은 환경에 따라 적용되며, Claude Code 판의 AML 훅과 동일한 차단을 보장하지 않습니다. 비밀키가 담긴 `.env` 파일 커밋, 버그 수정 중 테스트 파일 변경, 강제 푸시·하드 리셋에 대해서는 스킬에서 주의사항만 안내하므로, 실행 전에 직접 확인하세요.
- **독립 확인** — 기본은 같은 세션 안에서 수행하는 **자체 검증**입니다. 별도 에이전트에게 실제로 검증을 맡겼을 때만 `progress.md`에 "독립 확인"이라고 기록합니다.
- **사용량 측정** — Codex 세션 기록(`~/.codex/sessions/`)에서 현재 작업에 사용한 토큰 수를 읽어 작업 지표를 기록합니다. 현재 세션을 확실히 찾지 못하거나 작업 시작 시점의 기록이 없으면 `측정: 기록 없음`으로 표시합니다. 다른 세션의 값으로 대신 채우지 않습니다. 단가를 확인한 모델만 비용을 계산하고, 나머지는 "비용 미산정"으로 표시합니다. 자세한 기준은 [작업 지표 측정 기준](aml/references/telemetry.md)을 참고하세요.
- **Langfuse 전송** — Codex 판 첫 버전에서는 지원하지 않습니다.

## Claude Code에서 진행하던 프로젝트를 Codex로 옮길 때

기존 계획·기록 파일을 그대로 사용하고, Codex용 프로젝트 안내 파일을 준비합니다.

1. 프로젝트 폴더에 `spec.md`·`task.md`·`progress.md`가 있고, `CLAUDE.md`의 "확인하는 법"에 실행·테스트 명령이 있는지 확인합니다.
2. `AGENTS.md`가 **없을 때만** Codex에 이렇게 요청합니다: "spec.md·task.md·progress.md는 그대로 두고, CLAUDE.md의 내용(특히 확인하는 법)을 옮겨서 aml의 AGENTS 템플릿 형식에 맞춰 AGENTS.md만 만들어 줘. 다른 파일은 바꾸지 마."
3. `$aml:doctor`로 점검합니다.
4. `$aml:go`로 이어서 진행합니다.

`AGENTS.md`가 이미 있으면 그대로 두고, `CLAUDE.md`와 다른 점이 있으면 어느 쪽이 맞는지 확인해 직접 수정합니다. `REVIEW.md`는 두 도구에서 함께 사용합니다. `.claude/skills/`의 규칙 카드는 Codex가 읽지 않으므로, 계속 적용할 규칙만 `$aml:rule`로 다시 작성합니다. 한 번에 한 도구만 사용하고, 전환하기 전에 커밋해 두세요. 자세한 내용은 [도구 전환 안내](aml/references/switching.md)를 참고하세요.

반대 방향(Codex → Claude Code)으로 옮길 때는 [Claude Code 판 안내](../claude-code/README.md#codex에서-진행하던-프로젝트를-claude-code로-옮길-때)를 보세요.

## 테스트 (저장소 수정 시)

```bash
bash codex/tests/test-templates.sh   # 두 판의 공통 템플릿 5개 일치 여부 확인
python3 codex/tests/test_observe.py  # 측정·요약 숫자 검사
bash codex/tests/test-package.sh     # 패키지 구조 (codex 명령이 있으면 격리 설치와 스킬 목록까지)
```
