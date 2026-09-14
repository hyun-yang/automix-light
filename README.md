# automix-light (aml)

> automix 의 가벼운 버전. 첫 앱을 만드는 사람을 위한 Claude Code 플러그인 — 명령도 산출물도 전부 한국어입니다.

Anthropic 의 [AI-Native SDLC 플레이북](https://claude.com/blog/the-ai-native-sdlc-playbook)을 **혼자 만드는 사람 크기로** 옮겼습니다. 뼈대는 한 문장입니다 — *단계마다 파일 하나를 남기고, 다음 단계는 그 파일을 읽고 시작한다.*

```text
intent.md  →  spec.md  →  task.md  →  코드 + progress.md  →  리뷰  →  다음 intent.md
왜 만드나    무엇 + 완성기준  계획(파일·위험·증명)   한 일 + 측정      약속 지켰나    한 바퀴 더
```

## 설치

준비물: [Claude Code](https://claude.com/claude-code), bash, `python3`(관측 스크립트용 — 없어도 구현은 진행됩니다).

```bash
git clone https://github.com/hyun-yang/automix-light.git
cd automix-light
./install.sh          # ~/.claude-marketplaces/automix-light 로 복사됩니다
```

그다음 Claude Code 안에서:

```text
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

`/help` 에 `/aml:new` 부터 `/aml:doctor` 까지 보이면 끝입니다.

## 명령 7개

| 명령 | 하는 일 |
|---|---|
| `/aml:new "한 줄 아이디어"` | 인터뷰로 구체화 → `intent.md` · `spec.md` · `task.md` · `progress.md` 생성 |
| `/aml:go` | `task.md` 를 순서대로 구현·검증·기록, 할 일마다 커밋 |
| `/aml:review` | 커밋 전 버그 · 안전 · 약속 지킴 3패스 (코드는 고치지 않음) |
| `/aml:next` | 써 본 결과를 다음 바퀴로 — 작은 건 할 일로, 큰 건 새 의도로 |
| `/aml:rule` | 두 번 나온 실수를 규칙 카드로 굳히기 |
| `/aml:status` | 진행 상황과 지표(완성 기준 통과율 · 누적 시간·비용) |
| `/aml:doctor` | 시작 전 점검 (읽기 전용) |

## 특징

- **md 우선** — 명령·템플릿·산출물이 전부 마크다운. 예외는 관측 스크립트 하나(`aml/scripts/observe.py`, 파이썬 표준 라이브러리만)와 안전망 훅 하나(`aml/hooks/aml-guard.sh`).
- **안전망** — 되돌리기 어려운 일 세 가지(`.env` 커밋 · 버그 고치는 중 테스트 파일 수정 · 강제 푸시/하드 리셋)를 막습니다. `spec.md` 와 `task.md` 가 있는 폴더에서만 동작하므로 다른 저장소에는 영향이 없습니다.
- **독립 확인** — 다 만들었다고 하면 `verifier` 도우미가 새 눈으로 직접 실행해 확인합니다.
- **측정 기록** — 할 일마다 모델·소요 시간·토큰·예상 비용이 `progress.md` 에 한 줄로 남습니다. [Langfuse](https://langfuse.com) 전송은 선택이며 **기본 꺼짐**입니다.

## 저장소 구조

```text
.claude-plugin/marketplace.json   마켓플레이스 정의
aml/                              플러그인 본체
  commands/                       /aml:* 명령 7개
  agents/verifier.md              독립 확인 도우미
  hooks/aml-guard.sh              안전망 (PreToolUse 훅)
  scripts/observe.py              측정 기록 (표준 라이브러리만)
  templates/                      intent · spec · task · progress · review 서식
  references/                     더 깊은 설명
install.sh                        마켓플레이스 설치 도구
tests/                            스모크 테스트
```

## 테스트

```bash
bash tests/e2e-smoke-guard.sh     # 안전망 6케이스
bash tests/e2e-smoke-observe.sh   # 측정 기록 + 설치본 확인
```

## 더 보기

- [`aml/README.md`](aml/README.md) — 각 명령의 자세한 동작, 인터뷰 방식, Langfuse 설정
- [`aml/Example.md`](aml/Example.md) — 한 바퀴 전체 예시
- [`aml/references/`](aml/references/) — 산출물 사슬 · 안전망 직접 추가하기 · 다음 단계

## 라이선스

[MIT](LICENSE)
