# 다음 단계 — 혼자에서 여럿으로

**지금 필요한 문서가 아니다.** 혼자 만들 때는 aml 의 명령 7개면 충분하다. 아래는 "이런 게 필요해졌다" 싶을 때 무엇을 보면 되는지 적어 둔 지도다. 필요해지기 전에 도입하면 짐만 된다.

## 1. 동시에 여러 창

**언제** — 서로 다른 파일을 건드리는 할 일이 두세 개 밀려 있을 때.

`git worktree` 로 같은 저장소를 폴더 두 개로 펼치면, 창마다 다른 작업을 시킬 수 있다.

```bash
git worktree add ../myapp-작업2 -b 작업2
# 새 터미널에서 그 폴더를 열고 claude 실행
```

두세 개가 현실적인 한계다 — 늘리는 기준은 "내가 결과를 제대로 볼 수 있는 만큼"이다. task.md 를 보고 **바뀌는 파일이 겹치지 않는** 할 일만 나눈다. 겹치면 한 창에서 순서대로 한다.

## 2. 자동 확인 (CI)

**언제** — 손으로 테스트 돌리는 걸 잊기 시작할 때, 또는 다른 사람과 같이 만들 때.

GitHub 저장소라면 `.github/workflows/check.yml` 하나로 시작한다.

```yaml
name: 확인
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test      # CLAUDE.md 의 "확인하는 법" 명령을 그대로
```

한 걸음 더: 실패했을 때 Claude 에게 원인을 요약시킬 수 있다(`claude -p "..."` 로 대화 없이 실행). 그리고 **CLAUDE.md·규칙 카드·안전망을 고쳤을 때**도 확인을 한 번 돌리는 게 좋다 — Claude 를 이끄는 설정이 바뀌면 결과도 달라지기 때문이다. `/aml:doctor` 가 그 시점을 알려 준다.

문서: `code.claude.com/docs/en/github-actions`

## 3. 정기 점검

**언제** — 만든 지 한 달이 지났을 때, 또는 남에게 보여 주기 전에.

`/aml:review 전체` 로 코드 전체를 한 번 훑는다. 새로 만든 것 말고 **예전에 만든 것**에서 위험한 게 없는지 보는 게 목적이다. 찾은 것은 작으면 task.md 로, 크면 intent.md 로 보낸다 — 새로 만드는 것과 같은 길로 간다.

회사 저장소라면 예약 스캔(Claude Security)을 붙일 수 있다. 관리자가 켜야 하고 유료다.

## 4. 여러 사람이 같이 만들 때

**언제** — 두 번째 사람이 들어올 때.

- `REVIEW.md` 를 그대로 팀 기준으로 쓴다. 사람마다 다르게 보던 것을 한 기준으로 맞추는 게 첫 이득이다.
- PR 에 Claude 리뷰를 붙인다(관리형 Code Review 또는 `claude-code-action`). 사람은 "의도와 위험"을 보고, 기계는 "빠뜨린 것"을 본다.
- 리뷰에서 같은 지적이 두 번 나오면 `/aml:rule` 로 규칙을 만든다. 팀에서는 이게 특히 크다 — 사람마다 반복하던 실수가 한 번에 사라진다.

## 5. 회사 규칙을 강제해야 할 때

**언제** — 회사 저장소에서, 개인이 끌 수 없는 규칙이 필요할 때.

관리자가 배포하는 설정(managed settings)으로 개인 설정보다 위에서 강제할 수 있다. 예:

```json
{
  "permissions": {
    "deny": ["Read(.env*)", "Read(./secrets/**)", "Bash(curl *)"],
    "allow": ["Bash(git *)", "Bash(npm test)"]
  },
  "allowManagedHooksOnly": true,
  "allowManagedMcpServersOnly": true
}
```

- `deny` — 비밀 파일을 아예 못 읽게, 바깥으로 못 내보내게
- `allow` — 안전한 명령은 미리 허용해서 매번 묻지 않게
- `allowManagedHooksOnly` / `allowManagedMcpServersOnly` — 개인이 안전망이나 도구를 추가·해제하지 못하게

문서: `code.claude.com/docs/en/settings`, `code.claude.com/docs/en/permissions`, `code.claude.com/docs/en/sandboxing`

## 6. Slack 에서 부르기

**언제** — 문제가 채팅으로 들어오기 시작할 때.

Claude 를 채널 멤버로 넣으면(Claude Tag) 급한 일이 올라온 자리에서 바로 살펴보고, 작은 건 PR 로 올리고 큰 건 정리해 준다. 대화가 그대로 기록이 된다.

## 7. 대시보드로 보기

**언제** — "얼마나 쓰고 있지?"가 궁금해질 때.

aml 은 이미 할 일마다 측정 줄을 남기고, `/aml:status` 가 합쳐서 보여 준다. 웹 대시보드로 보고 싶으면 Langfuse 를 켠다(README 의 "Langfuse 켜기"). 회사 차원의 사용량·비용 집계는 OpenTelemetry 로 내보낸다: `code.claude.com/docs/en/monitoring-usage`

## 8. am 으로 갈아타기

**언제** — 앱을 꾸준히 만들게 되고, 한 번에 여러 기능이 돌아갈 때.

`am`(automix)에는 독립 검증 관문, 팀 실행(여러 에이전트), 프로젝트를 넘나드는 패턴 라이브러리, 예산 상한, 되돌리기 명령이 들어 있다. 기획 → 할 일 → 검증이라는 뼈대가 같아서 aml 에서 익힌 흐름이 그대로 이어진다.
