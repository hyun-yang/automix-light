# 프로젝트 확장과 팀 협업

앱의 규모가 커지거나 함께 개발하는 사람이 늘어나면 추가 도구가 필요할 수 있습니다. 이 문서는 병렬 작업, 자동 검증, 팀 규칙 등을 도입할 시점과 시작 방법을 안내합니다. 현재 작업에 필요한 항목부터 선택해 적용하세요.

## 1. 여러 작업을 동시에 진행하기

**도입 시점:** 서로 다른 파일을 수정하는 작업이 두세 개 있고, 각각 독립적으로 진행할 수 있을 때입니다.

`git worktree`로 같은 저장소의 별도 작업 폴더를 만들면 터미널 창마다 다른 브랜치에서 작업할 수 있습니다.

```bash
git worktree add ../myapp-작업2 -b 작업2
# 새 터미널에서 생성한 폴더를 열고 claude 실행
```

처음에는 두세 개 정도로 시작하고, 결과를 충분히 검토할 수 있는 범위에서 조정합니다. `task.md`를 보고 **변경할 파일이 겹치지 않는 작업**을 나눕니다. 같은 파일을 수정해야 한다면 순서대로 진행합니다.

## 2. 자동 검증 (CI)

**도입 시점:** 수동 테스트를 빠뜨리기 시작하거나 다른 사람과 함께 개발할 때입니다.

CI는 코드를 푸시하거나 PR을 만들 때 테스트 등을 자동으로 실행하는 방식입니다. GitHub 저장소라면 `.github/workflows/check.yml`에 다음과 같은 설정을 추가해 시작할 수 있습니다. 아래는 npm을 사용하는 프로젝트의 예시입니다.

```yaml
name: 확인
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test      # 프로젝트의 설치·테스트 명령으로 변경
```

프로젝트에 맞는 명령은 `CLAUDE.md`의 “확인하는 법”을 참고합니다. 필요하면 `claude -p "..."`로 Claude를 비대화형으로 실행해 실패 원인을 요약하도록 구성할 수도 있습니다.

`CLAUDE.md`, 규칙 카드, 작업 차단 훅을 변경했을 때도 검증을 실행하는 것이 좋습니다. 이 설정들이 Claude의 작업 방식에 영향을 주기 때문입니다. `/aml:doctor`는 설정 변경 후 검증 여부를 확인합니다.

참고: [Claude Code의 GitHub Actions 안내](https://code.claude.com/docs/en/github-actions)

## 3. 정기 코드 점검

**실행 시점:** 개발 후 한 달 정도 지났거나 다른 사람에게 앱을 공개하기 전입니다.

`/aml:review 전체`로 기존 코드를 포함한 전체 코드를 점검합니다. 작은 수정은 `task.md`에 추가하고, 큰 변경은 `intent.md`에 정리해 기획과 구현 절차로 이어갑니다.

회사 저장소에서 예약 보안 검사를 도입하려면 Claude Security 같은 도구의 이용 조건과 관리자 설정을 확인합니다.

## 4. 팀의 리뷰 기준 공유

**도입 시점:** 다른 사람이 프로젝트에 참여하기 시작할 때입니다.

- `REVIEW.md`를 팀의 공통 리뷰 기준으로 사용합니다. 리뷰어마다 확인 범위가 달라지는 것을 줄일 수 있습니다.
- 필요하면 PR에 Claude 리뷰를 연동합니다. 관리형 Code Review나 `claude-code-action`을 검토할 수 있습니다. 자동 리뷰 결과와 함께 변경 목적, 설계 판단, 위험을 사람이 확인합니다.
- 같은 지적이 두 번 반복되면 `/aml:rule`로 개발 규칙을 작성합니다. 팀원들이 같은 기준을 참고해 유사한 실수를 줄일 수 있습니다.

## 5. 조직 공통 설정 적용

**도입 시점:** 회사 저장소에서 개인이 해제할 수 없는 공통 규칙이 필요할 때입니다.

관리자가 배포하는 설정(managed settings)을 사용하면 조직 차원의 권한과 도구 사용 정책을 적용할 수 있습니다. 다음은 설정 예시입니다.

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

- `deny` — 지정한 파일 읽기와 명령 실행을 차단합니다. 위 예시는 `.env*`, `./secrets/**` 읽기와 `curl` 명령을 대상으로 합니다.
- `allow` — 지정한 명령을 매번 승인하지 않아도 실행할 수 있도록 허용합니다.
- `allowManagedHooksOnly` / `allowManagedMcpServersOnly` — 훅과 MCP 서버의 사용 범위를 관리자가 허용한 설정으로 제한합니다.

참고: [설정](https://code.claude.com/docs/en/settings), [권한](https://code.claude.com/docs/en/permissions), [샌드박스](https://code.claude.com/docs/en/sandboxing)

## 6. Slack 연동 검토

**도입 시점:** 버그 보고나 개발 요청을 주로 Slack에서 받을 때입니다.

Slack에서 Claude를 호출해 보고된 문제를 살펴보고, 수정 작업이나 PR 작성으로 연결하는 방식을 검토할 수 있습니다. 도입 전에는 사용 가능한 연동 기능과 저장소 접근 권한을 확인합니다.

## 7. 대시보드에서 작업 지표 확인

**도입 시점:** 모델 사용량과 비용을 여러 작업에 걸쳐 비교하고 싶을 때입니다.

aml은 작업별 지표를 기록하며 `/aml:status`에서 누적 결과를 보여 줍니다. 웹 대시보드가 필요하면 [Langfuse 연동](../README.md#langfuse-연동-선택-사항)을 설정합니다.

조직 전체의 사용량과 비용을 집계하려면 OpenTelemetry를 통한 데이터 전송도 검토할 수 있습니다. 설정 방법은 [사용량 모니터링 문서](https://code.claude.com/docs/en/monitoring-usage)를 참고하세요.

## 8. automix(am)로 전환

**전환 시점:** 여러 기능을 지속적으로 개발하면서 더 많은 작업 관리 기능이 필요할 때입니다.

`am`(automix)은 별도의 검증 단계, 여러 에이전트의 협업, 프로젝트 간 개발 패턴 공유, 예산 상한, 되돌리기 명령을 제공합니다. 기획 → 작업 계획 → 구현·검증이라는 기본 흐름이 같아 aml에서 익힌 방식을 이어서 사용할 수 있습니다.
