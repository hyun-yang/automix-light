# automix-light (aml)

> 첫 앱을 만드는 사람을 위한 Claude Code 플러그인입니다. automix를 가볍게 구성한 한국어 버전으로, 기획부터 구현, 검증, 사용 후 개선까지 안내합니다.

Anthropic의 [AI-Native SDLC 플레이북](https://claude.com/blog/the-ai-native-sdlc-playbook)을 바탕으로, **혼자 앱을 만드는 사람도 따라갈 수 있도록 개발 절차를 간소화했습니다.** 핵심은 각 단계의 결과를 문서로 남기고, 다음 단계에서 그 문서를 기준으로 작업하는 것입니다.

아이디어를 구체화하고, 구현 계획을 세우고, 앱을 만든 뒤 검증합니다. 완성된 앱을 직접 사용하면서 발견한 문제와 필요한 기능은 다음 작업에 반영합니다.

| 단계 | 기록하는 내용 |
|---|---|
| 기획 (`intent.md`) | 앱을 만드는 목적과 해결하려는 문제 |
| 요구사항 정의 (`spec.md`) | 필요한 기능과 완성 기준 |
| 작업 계획 (`task.md`) | 작업 순서, 변경할 파일, 예상 위험, 검증 방법 |
| 구현 및 검증 (코드 + `progress.md`) | 구현 결과, 검증 결과, 소요 시간과 비용 |
| 코드 리뷰 | 버그, 보안 문제, 요구사항 충족 여부 |
| 사용 후 개선 | 작은 수정은 `task.md`에 추가하고, 새 기능이나 방향 변경은 `intent.md`에 정리 |

## 설치

필요한 도구는 [Claude Code](https://claude.com/claude-code)와 bash입니다. 작업 지표를 기록하려면 `python3`도 필요하지만, 없어도 구현은 진행할 수 있습니다.

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
./install.sh          # ~/.claude-marketplaces/automix-light에 복사합니다
```

설치 스크립트를 실행한 뒤, Claude Code에서 다음 명령을 입력합니다.

```text
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

`/help`에 `/aml:new`, `/aml:go` 등 아래 명령 7개가 표시되면 설치가 완료된 것입니다.

## 명령어

| 명령 | 하는 일 |
|---|---|
| `/aml:new "한 줄 아이디어"` | 질문과 답변으로 아이디어를 구체화하고 `intent.md`, `spec.md`, `task.md`, `progress.md` 생성 |
| `/aml:go` | `task.md`의 작업을 순서대로 구현·검증하고, 결과를 기록한 뒤 작업별로 커밋 |
| `/aml:review` | 커밋 전에 버그, 보안 문제, 요구사항 충족 여부를 점검하고 결과 보고 (코드는 수정하지 않음) |
| `/aml:next` | 앱을 사용하며 발견한 문제와 필요한 기능을 정리해, 작은 수정은 작업 목록에 추가하고 큰 변경은 새 기획으로 정리 |
| `/aml:rule` | 반복된 실수를 예방할 수 있도록 개발 규칙을 문서로 작성 |
| `/aml:status` | 진행 상황, 완성 기준 통과율, 누적 시간과 비용 확인 |
| `/aml:doctor` | 작업을 시작할 준비가 되었는지 점검 (파일은 수정하지 않음) |

## 특징

- **마크다운 중심 구성** — 명령어 정의, 템플릿, 작업 결과를 마크다운 파일로 관리합니다. 실행 코드는 작업 지표를 기록하는 스크립트(`aml/scripts/observe.py`, 파이썬 표준 라이브러리만 사용)와 위험한 작업을 차단하는 훅(`aml/hooks/aml-guard.sh`)으로 구성됩니다.
- **위험한 작업 차단** — `.env` 파일 커밋, 버그 수정 중 테스트 파일 변경, 강제 푸시와 하드 리셋을 막습니다. `spec.md`와 `task.md`가 있는 폴더에서만 동작합니다.
- **별도의 검증 담당 에이전트** — 구현이 끝나면 `verifier` 에이전트가 직접 실행해 완성 기준을 충족하는지 확인합니다.
- **작업 지표 기록** — 작업별 모델, 소요 시간, 토큰 사용량, 예상 비용을 `progress.md`에 기록합니다. [Langfuse](https://langfuse.com)로 지표를 전송하는 기능은 선택 사항이며, **기본적으로 비활성화되어 있습니다.**

## 저장소 구조

```text
.claude-plugin/marketplace.json   마켓플레이스 설정
aml/                              플러그인 파일
  commands/                       /aml:* 명령어 7개
  agents/verifier.md              검증 담당 에이전트
  hooks/aml-guard.sh              위험한 작업 차단 (PreToolUse 훅)
  scripts/observe.py              작업 지표 기록 (표준 라이브러리만 사용)
  templates/                      intent · spec · task · progress · review 템플릿
  references/                     추가 설명과 활용 안내
install.sh                        마켓플레이스 설치 스크립트
tests/                            기본 동작 확인 테스트
```

## 테스트

```bash
bash tests/e2e-smoke-guard.sh     # 위험한 작업 차단: 6가지 사례 확인
bash tests/e2e-smoke-observe.sh   # 작업 지표 기록 및 설치 결과 확인
```

## 더 보기

- [`aml/README.md`](aml/README.md) — 명령어별 동작, 기획 질문 방식, Langfuse 설정
- [`aml/Example.md`](aml/Example.md) — 기획부터 구현, 검증, 개선까지의 전체 예시
- [`aml/references/`](aml/references/) — 단계별 문서의 연결 방식, 작업 차단 규칙 추가, 확장 방법

## 라이선스

[MIT](LICENSE)
