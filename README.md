# automix-light (aml)

> 첫 앱을 만드는 사람을 위한 Claude Code · Codex 플러그인입니다. automix를 가볍게 구성한 한국어 버전으로, 기획부터 구현, 검증, 사용 후 개선까지 안내합니다.

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

명령어 정의, 템플릿, 작업 결과는 모두 마크다운 파일입니다. 실행 코드는 작업 지표를 기록하는 스크립트(`observe.py`, 파이썬 표준 라이브러리만 사용)와 Claude Code 판의 차단 훅(`aml-guard.sh`)뿐입니다.

## 어느 도구에서 쓰나요?

같은 흐름을 두 도구에서 쓸 수 있습니다. 쓰는 도구의 폴더로 가서 설치 안내를 따르세요.

| 쓰는 도구 | 설치와 안내 | 설치 명령 (저장소 루트에서) |
|---|---|---|
| Claude Code | [`claude-code/README.md`](claude-code/README.md) | `bash claude-code/install.sh` |
| Codex | [`codex/README.md`](codex/README.md) | `codex plugin marketplace add "$PWD/codex"` → `codex plugin add aml@automix-light` |

> 설치 명령이 바뀌었습니다. 예전의 `./install.sh` 대신 저장소 루트에서 `bash claude-code/install.sh` 를 실행합니다.

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
```

## 명령어

| 하는 일 | Claude Code | Codex |
|---|---|---|
| 질문과 답변으로 아이디어를 구체화하고 `intent.md`, `spec.md`, `task.md`, `progress.md` 생성 | `/aml:new "한 줄 아이디어"` | `$aml:new` |
| `task.md`의 작업을 순서대로 구현·검증하고, 결과를 기록한 뒤 작업별로 커밋 | `/aml:go` | `$aml:go` |
| 커밋 전에 버그, 보안 문제, 요구사항 충족 여부를 점검 (코드는 수정하지 않음) | `/aml:review` | `$aml:review` |
| 앱을 사용하며 발견한 문제와 필요한 기능을 다음 작업이나 새 기획으로 정리 | `/aml:next` | `$aml:next` |
| 반복된 실수를 예방하는 개발 규칙 작성 | `/aml:rule` | `$aml:rule` |
| 진행 상황, 완성 기준 통과율, 누적 시간과 비용 확인 | `/aml:status` | `$aml:status` |
| 작업을 시작할 준비가 되었는지 점검 (파일은 수정하지 않음) | `/aml:doctor` | `$aml:doctor` |

계획·기록 파일(`intent.md`·`spec.md`·`task.md`·`progress.md`·`REVIEW.md`)은 두 도구에서 같은 모양이라, 하던 프로젝트를 다른 도구로 옮겨 이어서 진행할 수 있습니다. 다른 것은 프로젝트 안내 파일(`CLAUDE.md` ↔ `AGENTS.md`)과 규칙 카드 위치(`.claude/skills/` ↔ `.agents/skills/`)뿐입니다. 옮기는 절차는 각 폴더의 README 에 있습니다. 한 번에 한 도구만 쓰세요.

## 두 판의 차이

| | Claude Code 판 | Codex 판 |
|---|---|---|
| 위험한 작업 차단 | AML 훅이 `.env` 커밋, 버그 수정 중 테스트 파일 변경, 강제 푸시·하드 리셋을 막음 | 이 버전에는 AML 전용 차단 훅이 없습니다. Codex 의 권한·샌드박스·승인 설정은 환경에 따라 적용되며, Claude 판 AML 훅과 같은 차단을 보장하지 않습니다 |
| 마지막 확인 | 별도 검증 에이전트(`verifier`)가 직접 실행해 확인 | 기본은 자체 확인. 실제로 따로 맡겼을 때만 "독립 확인"으로 기록 |
| 작업 지표 | 모델, 소요 시간, 토큰, 예상 비용. [Langfuse](https://langfuse.com) 전송은 선택 사항이며 **기본 꺼짐** | 모델, 소요 시간, 토큰. 확실히 읽지 못하면 `측정: 기록 없음`. 단가를 확인하지 않은 모델은 "비용 미산정". Langfuse 전송 없음 |

## 저장소 구조

```text
README.md                           이 문서 — 도구 고르기
claude-code/                        Claude Code 판
  .claude-plugin/marketplace.json   마켓플레이스 설정
  aml/                              플러그인 (commands · agents · hooks · scripts · templates · references)
  install.sh                        마켓플레이스 설치 스크립트
  tests/                            기본 동작 확인 테스트
  docs/archive/                     지난 분석 문서
codex/                              Codex 판
  .agents/plugins/marketplace.json  마켓플레이스 설정
  aml/                              플러그인 (skills · scripts · templates · references)
  tests/                            템플릿 일치 · 측정 · 패키지 구조 검사
  docs/                             설계 분석과 검토 문서
```

두 `aml/` 폴더는 서로를 참조하지 않습니다. 공통 템플릿 5개(spec · task · progress · intent · review)는 두 판에 같은 내용으로 들어 있고, `codex/tests/test-templates.sh` 가 같은지 확인합니다.

## 테스트

```bash
bash claude-code/tests/e2e-smoke-guard.sh     # 위험한 작업 차단: 6가지 사례 확인
bash claude-code/tests/e2e-smoke-observe.sh   # 작업 지표 기록 및 설치 결과 확인
bash codex/tests/test-templates.sh            # 공통 템플릿이 두 판에서 같은지
python3 codex/tests/test_observe.py           # Codex 측정·요약 숫자 검사
bash codex/tests/test-package.sh              # Codex 패키지 구조 (codex 명령이 있으면 격리 설치까지)
```

## 더 보기

- [`claude-code/aml/README.md`](claude-code/aml/README.md) — 명령어별 동작, 기획 질문 방식, Langfuse 설정
- [`claude-code/aml/Example.md`](claude-code/aml/Example.md) — 기획부터 구현, 검증, 개선까지의 전체 예시
- [`claude-code/aml/references/`](claude-code/aml/references/) — 단계별 문서의 연결 방식, 작업 차단 규칙 추가, 확장 방법
- [`codex/aml/references/`](codex/aml/references/) — Codex 판의 도구 전환 준비, 완성 기준 확인, 측정 기준

## 라이선스

[MIT](LICENSE)
