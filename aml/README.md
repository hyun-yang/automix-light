# automix-light (aml)

> automix의 라이트판. 초보자가 원하는 건 한 가지 — **빠르고 정확한 구현**.

automix(am)는 스펙 검증·코드 리뷰·팀 모드·패턴 라이브러리·외부 관측까지 갖춘 풀 하니스입니다. 처음 앱을 만드는 사람에게 그 대부분은 아직 필요 없습니다. automix-light는 그중 초보자에게 꼭 필요한 것만 남겼습니다:

- **파일 3개** — `spec.md`(무엇을 만드나), `task.md`(할 일), `progress.md`(진행 기록). 전부 프로젝트 루트에, 전부 쉬운 한국어로.
- **명령 4개** — `/aml:new` → `/aml:go` → `/aml:status`, 그리고 점검용 `/aml:doctor`.
- **md-first** — 명령·템플릿·산출물은 전부 마크다운입니다. 유일한 예외는 관측 스크립트 `scripts/observe.py` 하나(파이썬 표준 라이브러리만) — 태스크마다 모델·소요 시간·토큰·예상 비용을 재서 progress.md에 남기고, 원하면 Langfuse로도 보냅니다. 이 스크립트가 실패해도 구현은 절대 멈추지 않습니다.

설계의 뿌리는 "A Field Guide to Fable": 작은 프롬프트, 맥락 우선, 그리고 **시작 전에 미지를 캐기**. 초보자는 뭘 모르는지도 모르는(Unknown Unknowns) 상태에서 시작합니다 — 그래서 첫 명령이 구현이 아니라 인터뷰입니다.

## 설치

```bash
cd automix-light
./install.sh          # ~/.claude-marketplaces/automix-light 로 스테이징
```

그다음 Claude Code 안에서:

```
/plugin marketplace add ~/.claude-marketplaces/automix-light
/plugin install aml@automix-light
```

`/help`에 `/aml:new`, `/aml:go`, `/aml:status`, `/aml:doctor`가 보이면 성공입니다.

## 사용 흐름

### 1. `/aml:new "만들고 싶은 것 한 줄"`

Claude가 인터뷰로 여러분의 지도를 만듭니다. 네 영역을 차례로 캐냅니다:

| 영역 | 뜻 | 꺼내는 방법 |
|---|---|---|
| KK (아는 앎) | 이미 말한 것 | 정리만 |
| UU (모르는 모름) | 고려조차 못 한 결정 | "보통 이런 걸 정해요" 목록으로 먼저 보여주기 |
| KU (아는 모름) | 정해야 하는데 안 정한 것 | 보기 있는 질문, "추천해줘" 가능 |
| UK (모르는 앎) | 말로 못 하지만 보면 아는 것 | 스타일 다른 시안 3~4개를 보고 고르기 |

끝나면 `spec.md`(완성 기준 체크리스트 포함)와 `task.md`가 생기고, 여러분의 확인을 받습니다.

### 2. `/aml:go`

`task.md`를 순서대로 구현합니다. 태스크마다:

1. **구현** — spec.md의 결정과 참조를 지도 삼아.
2. **검증** — 테스트 또는 실제 실행으로 동작 확인.
3. **기록** — `progress.md` 맨 위에 항목 추가: 한 일 / 검증 / **구현 노트**(계획과 다르게 한 것과 이유) / **측정** / 다음.

**측정 줄**이 이번 판의 새 기능입니다 — 태스크마다 이렇게 남습니다:

```
- 측정: claude-opus-4-8 · 4분 32초 · 토큰 입력 12.3k / 출력 4.1k (캐시 읽기 88k / 쓰기 2.1k) · 예상 비용 $0.42
```

읽는 법: 어떤 모델이 · 얼마나 오래 · 얼마나 많은 토큰(대화량)을 써서 이 태스크를 끝냈고, 대략 얼마짜리 작업이었는지. 비용은 공개 단가 기반 추정치로 청구서와 다를 수 있습니다. python3가 없는 환경에서는 이 줄이 `측정: 수집 불가`로 남지만 구현은 계속됩니다.

같은 문제에 3번 막히면 멈추고 여러분에게 묻습니다. 다 끝나면 `spec.md`의 완성 기준을 하나씩 실제로 확인한 뒤 보고합니다.

### 3. `/aml:status`

지금 어디까지 왔는지, 막힌 건 없는지, 다음에 뭘 하면 되는지 요약합니다. 원하면 **퀴즈**로 — 만든 것을 남에게 설명할 수 있는지 확인합니다.

### 4. `/aml:doctor`

시작 전(또는 뭔가 이상할 때) 상태 점검입니다. 읽기 전용 — 아무것도 고치지 않습니다.

- ❌ **막는 것**: spec.md/task.md/progress.md 없음, 완성 기준·태스크 체크박스 없음 → `/aml:new` 안내
- ⚠️ **안내만**: git 없음, python3 없음(측정 줄이 생략됨), Langfuse 설정 문제

Langfuse는 어떤 경우에도 진행을 막지 않습니다.

## Langfuse 켜기 (선택, 기본 꺼짐)

[Langfuse](https://langfuse.com)는 LLM 작업을 대시보드로 보는 관측 도구입니다. 켜면 태스크마다 측정 데이터(모델·토큰·시간·검증 결과)가 전송되어, 기능별로 묶인 타임라인을 웹에서 볼 수 있습니다. **안 켜도 아무 차이 없습니다** — progress.md 기록은 항상 남습니다.

1. Langfuse(클라우드 또는 자체 호스팅) 프로젝트에서 public/secret 키를 발급받습니다.
2. 키를 **환경변수로만** 설정합니다 (설정 파일에 넣지 마세요):
   ```bash
   export LANGFUSE_PUBLIC_KEY=pk-...
   export LANGFUSE_SECRET_KEY=sk-...
   export LANGFUSE_HOST=https://cloud.langfuse.com   # 자체 호스팅이면 그 주소
   ```
3. 프로젝트 루트에 `.aml/config.yaml`을 만듭니다:
   ```yaml
   langfuse: "on"        # "off" 또는 파일 없음 = 전송 안 함 (기본)
   langfuse_host: ""     # 비우면 LANGFUSE_HOST, 그것도 없으면 cloud.langfuse.com
   ```
4. `/aml:doctor`로 연결을 확인합니다 — "OK: Langfuse 연결 확인"이 보이면 끝.

전송은 best-effort입니다: 네트워크가 끊겨도, 키가 틀려도 경고 한 줄만 남기고 구현은 계속됩니다. 끄려면 `.aml/config.yaml`을 지우거나 `langfuse: "off"`로 바꾸면 됩니다.

## 예시 세션

```
/aml:new "칸반 형식 할 일 앱, HTML 파일 하나로"
  → "이런 걸 보통 정해요: 컬럼 수, 마감일, 완료된 카드의 행방, 드래그 이동…"
  → 질문 5개 (보기와 함께) → 시안 4개 → 3번 선택
  → spec.md + task.md 생성, 확인 요청

/aml:go
  → 1.1 보드 화면 → 검증 → progress.md 기록 (측정: claude-opus-4-8 · 3분 11초 · …)
  → 1.2 카드 추가 모달 → …
  → 완성 기준 7개 전부 확인 → "브라우저에서 todo.html 을 열어보세요"

/aml:status
  → "7개 중 7개 완료. 퀴즈로 확인해볼까요?"
```

## 언제 automix(am)로 졸업하나

앱을 **계속** 만들게 될 때입니다 — 독립 검증 게이트(goal), 코드 리뷰, 팀 실행, 프로젝트를 넘나드는 패턴 라이브러리가 필요해지면 am이 그 전부를 갖고 있습니다. spec → task → 검증이라는 뼈대는 같아서, aml에서 익힌 흐름이 그대로 이어집니다. am의 Langfuse 연동(`/am:observe`)도 같은 환경변수를 그대로 씁니다.
