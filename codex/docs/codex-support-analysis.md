# Claude Code와 Codex 동시 지원: 구조·문서 분석

2026-10-17 · 현재 저장소 기준 · 분석안이며 구현 계획 확정이나 구현 착수가 아님.

## 결론

**루트의 주요 구성을 `claude-code/`, `codex/`, `README.md`로 정리하는 구조를 권장한다.** 사용자가 선택한 방향이며, 기존 설치 스크립트와 테스트의 상대 경로를 재검토한 결과 이동 부담도 제한적이다. 앞선 “기존 `aml/`을 루트에 유지” 권고는 이 안으로 대체한다.

두 폴더는 각각 플랫폼의 배포·개발 영역이고, 내부 `aml/`이 설치되는 플러그인 패키지다. 공통 산출물의 형식과 개발 절차는 맞추되, 명령 진입점·프로젝트 지침·훅·세션 측정은 환경별로 관리한다. 폴더명은 공백 없는 `claude-code`를 사용한다.

단순히 Claude를 Codex로 바꾸는 문서 치환으로는 부족하다. 7개 명령을 스킬로 옮기는 작업 외에 설치, 독립 검증, 강제 차단, 사용량 수집의 차이를 처리해야 한다. 첫 지원 범위는 **로컬 Codex에서 기획→구현→검증→진행 기록을 사용하는 것**을 추천한다. 모든 Codex 실행 환경에서 기존 훅과 비용 측정까지 같다고 약속하는 것은 별도 검증이 필요하다.

Langfuse 제거는 취소된 결정대로 범위에 넣지 않는다. 기존 기본 off 동작을 유지한다.

## 현재 폴더 구조와 역할

```text
repository/
├── README.md                       저장소 소개·설치·구조
├── install.sh                      Claude marketplace용 복사·설치 안내
├── .claude-plugin/marketplace.json  ./aml을 등록
├── aml/
│   ├── .claude-plugin/plugin.json  v0.6.0, PreToolUse 훅 선언
│   ├── README.md / Example.md      상세 사용법·사용 예시
│   ├── commands/                   new, go, review, next, rule, status, doctor
│   ├── agents/verifier.md          Claude Task로 호출하는 검증 역할
│   ├── hooks/aml-guard.sh          Claude 도구 입력을 해석하는 차단 스크립트
│   ├── scripts/observe.py          Claude 세션 집계·로컬 요약·선택 전송
│   ├── templates/                 spec, task, progress, claude, intent, skill, review
│   └── references/                산출물 연결·자율성/안전망·다음 단계
└── tests/
    ├── e2e-smoke-guard.sh
    └── e2e-smoke-observe.sh
```

CodeGraph에는 Python 소스 1개가 인덱싱되어 있다. Markdown·shell·JSON 구조는 파일 목록 및 내용 조사로 보완했다. 프로젝트 루트에 `spec.md`, `task.md`, `progress.md`는 현재 없다.

## 이미 설치된 Codex판에서 얻을 수 있는 것

이 환경의 저장소 외부 캐시에 `0.2.0+codex.20260717122407` 버전의 AML이 있다. 현재 요청에 사용된 `aml-new`도 이 패키지의 스킬이다. **이 저장소에 Codex 지원이 들어 있다는 뜻은 아니다.**

- 캐시에는 `aml-new`, `aml-go`, `aml-status`, `aml-doctor` 4개 스킬만 있다. 현재 저장소의 `review`, `next`, `rule`에 대응하는 스킬은 없다.
- 캐시 README에는 Codex 누적 토큰의 차분 측정과 `.env.langfuse` 직접 읽기가 설명되어 있다. 현재 저장소는 Claude 사용량 집계 및 환경변수 인증 방식이다. 이는 설명상 차이이며 캐시 측정 코드를 검증한 결과는 아니다.
- 캐시 `aml-go`에는 현재 저장소의 `Task`/`aml:verifier` 호출과 동일한 독립 검증 절차가 없다.
- 따라서 캐시는 참고·재사용 후보로만 취급해야 한다. 전체 복사는 기능 누락과 설정 방식 변경을 함께 가져올 수 있다.
- 스킬의 설치 루트 설명도 검토해야 한다. `skills/<이름>/SKILL.md`에서 패키지 루트는 `parents[2]`이다. 캐시의 “grandparent” 표현만 따르면 `skills/`를 루트로 오해할 수 있으므로 실제 리소스 존재 여부로 확인하는 방식이 필요하다.

## 권장 구조

아래는 앞으로의 목표 구조다. 이번 조사에서는 디렉터리나 구현 파일을 생성하지 않았다.

```text
repository/
├── README.md                       공통 소개 + 플랫폼 선택
├── claude-code/
│   ├── README.md                   Claude 설치·업데이트·개발 안내
│   ├── install.sh                  기존 스크립트를 함께 이동
│   ├── .claude-plugin/marketplace.json
│   ├── aml/                        기존 패키지 내부 구조 유지
│   │   ├── .claude-plugin/plugin.json
│   │   ├── commands/ agents/ hooks/
│   │   ├── templates/ references/
│   │   ├── README.md / Example.md
│   │   └── scripts/observe.py
│   └── tests/                      기존 두 smoke test를 함께 이동
├── codex/
│   ├── README.md                   Codex 설치·업데이트·지원 범위
│   ├── docs/                       Codex 분석·개발·예시 문서
│   ├── tests/                      Codex 및 양쪽 산출물 호환성 검증
│   └── aml/                        독립적으로 설치 가능한 Codex 패키지
│       ├── .codex-plugin/plugin.json
│       ├── skills/
│       │   ├── aml-new/SKILL.md
│       │   ├── aml-go/SKILL.md
│       │   ├── aml-review/SKILL.md
│       │   ├── aml-next/SKILL.md
│       │   ├── aml-rule/SKILL.md
│       │   ├── aml-status/SKILL.md
│       │   └── aml-doctor/SKILL.md
│       ├── templates/              공통 템플릿 + agents.template.md
│       ├── references/             공통 절차 + Codex별 설명
│       └── scripts/                Codex 측정·공통 요약 연결: 범위 확정 후
├── LICENSE                         저장소 공통 파일은 예외
└── .gitignore                      저장소 공통 파일은 예외
```

루트에 `shared/`, `scripts/`, `docs/`, `tests/`를 새로 두지 않는다. 공통 소개와 간단한 플랫폼 비교는 루트 README에, 상세 안내와 개발 문서는 해당 플랫폼 폴더에 둔다. `.git/`, `.gitignore`, `LICENSE` 같은 저장소 관리 항목은 “주요 구성 세 개”의 예외로 본다. 향후 CI를 사용한다면 `.github/` 같은 서비스 지정 경로 역시 예외가 필요하다.

각 패키지는 템플릿·참고 자료·실행 스크립트를 자체 포함한다. 실행할 때 형제 플랫폼 폴더를 참조하거나 심볼릭 링크로 묶지 않는다. 플랫폼 하나만 복사해 설치해도 동작해야 한다.

공통 템플릿은 처음에는 의도적인 복사본으로 관리한다. 루트 README에 공통 산출물의 필수 항목과 변경 시 양쪽 반영 원칙을 적고, `codex/tests/`에서 양쪽 형식의 호환성을 확인한다. `CLAUDE.md`/`AGENTS.md`나 호출 문법이 다르므로 모든 파일의 바이트 일치를 강제하는 방식은 적절하지 않다. 초기에는 별도 생성기나 동기화 시스템을 만들지 않아도 된다.

Codex의 현재 공식 문서는 루트 `plugin.json`을 쓰는 portable 형식과 `.codex-plugin/plugin.json` 호환 형식을 모두 설명한다. 위 구조는 기존 캐시와 비교하기 쉬운 호환 형식의 제안이다. 실제 배포 방식이 정해지면 형식 하나를 주 기준으로 선택한다. 두 형식의 우선순위를 모른 채 설정을 중복 관리하지 않는다. [공식 패키징 문서](https://developers.openai.com/plugins/build/plugins)

**재검토 결과:** 폴더 분리는 탐색과 배포 범위를 명확하게 만들고 두 플랫폼을 동등하게 다룬다. 단점은 일부 문서·템플릿 중복과 기존 저장소 경로 변경이다. 지금처럼 규모가 작은 Markdown 중심 저장소에서는 이 비용을 감수할 만하다. 다만 폴더 분리 자체가 Codex 기능 호환성을 해결하는 것은 아니다.

## 이동 영향: 실제 수정이 필요한 것과 유지되는 것

| 현재 위치 → 제안 위치 | 재검토 결과 |
|---|---|
| `install.sh` → `claude-code/install.sh` | `SCRIPT_DIR`가 스크립트 자신의 위치를 기준으로 계산된다(`install.sh:11`). 관련 폴더를 함께 옮기면 복사 경로 로직은 유지 가능하다. “저장소 루트”를 가리키는 오류 안내는 수정한다. |
| `.claude-plugin/` → `claude-code/.claude-plugin/` | marketplace의 `source: ./aml`은 같은 marketplace 영역 안에서 `aml/`을 가리키므로 이동 후에도 그대로 둘 수 있다. 실제 설치로 검증할 항목이다. |
| `aml/` → `claude-code/aml/` | 패키지 내부 구조와 `${CLAUDE_PLUGIN_ROOT}` 기준 리소스 참조는 유지 가능하다. |
| `tests/` → `claude-code/tests/` | 두 테스트의 `HERE/../aml` 참조가 그대로 맞는다. observe 테스트의 `HERE/../install.sh`와 설치 복사본 검사 경로도 유지된다(`tests/e2e-smoke-observe.sh:161`). |
| 루트 README의 설치 명령 | `./install.sh`를 `bash claude-code/install.sh`로 바꾸거나 `cd claude-code` 후 실행하도록 안내한다. 기존 루트 명령은 더 이상 유효하지 않다. |
| 기존 로컬 설치 대상 | `~/.claude-marketplaces/automix-light`는 바꿀 필요가 없다. 복사 결과를 기존 `.claude-plugin/ + aml/` 형태로 유지하면 현재 안내의 marketplace 등록 위치도 유지할 수 있다. |
| 저장소 루트를 직접 등록하는 외부 사용법 | 루트 `.claude-plugin/`이 사라지므로 기존 Git URL·루트 경로 등록과의 호환성을 가정하면 안 된다. 이 저장소에 문서화된 로컬 복사 설치를 우선 보존하고, 직접 Git 등록을 지원하려면 별도 검증한다. |
| 문서·외부 링크 | 루트의 `aml/...`, `tests/...`, `install.sh` 링크와 외부 문서의 이전 경로를 새 위치로 안내한다. 기존 패키지 내부 상대 링크는 대상도 함께 이동하면 유지 가능하다. |

즉, **marketplace·installer·테스트의 내부 경로를 전부 다시 써야 한다는 앞선 평가는 과했다.** 관련 항목을 한 묶음으로 이동하면 상대 관계는 유지된다. 호환성 변경은 주로 저장소 진입 경로와 외부 링크에 집중된다. 설치 스크립트를 실행하거나 실제 파일을 이동한 검증은 아직 하지 않았다.

현재 루트의 분석 문서도 최종 구조에서는 정리해야 한다. 이 문서는 `codex/docs/`로, 취소된 Langfuse 제거 분석은 필요하면 `claude-code/docs/archive/`로 옮길 수 있다. `.codegraph/`는 로컬 분석 인덱스로 취급하고 배포에 넣지 않는다. 이번에는 사용자 자료를 이동하거나 삭제하지 않았다.

## 반드시 나누어야 할 부분

| 영역 | 현재 근거 | Codex 대응·위험 |
|---|---|---|
| 명령 실행 | `commands/*.md`의 `allowed-tools`, `$ARGUMENTS`, `/aml:*` | `skills/<name>/SKILL.md`의 이름·설명·본문으로 전환. 사용자 메시지를 입력으로 해석하고 Claude 전용 도구 이름을 그대로 요구하지 않는다. |
| 리소스 경로 | `new.md:40,63`, `go.md:31`의 `${CLAUDE_PLUGIN_ROOT}` | Codex 스킬 위치 기준 패키지 루트 해석. 임의 작업 디렉터리에서도 템플릿·스크립트 접근 검증. |
| 프로젝트 안내 | `new.md:23,71`, `go.md:8`의 `CLAUDE.md` | Codex는 `AGENTS.md`를 사용. 기존 파일을 덮어쓰지 않고 공통 실행·검증 정보의 중복과 충돌 방침을 정한다. |
| 규칙 카드 | `rule.md:23–32`의 `.claude/skills/` | Codex 프로젝트 규칙은 `.agents/skills/`로 구분. 플러그인 자체의 배포 스킬과 사용자 프로젝트에 만드는 규칙 카드를 혼동하지 않는다. |
| 독립 검증 | `go.md:41`, `agents/verifier.md`의 `Task` 호출 | 검증 절차를 공통 문서로 분리하고 Codex에서 사용 가능한 독립 실행 수단에 연결. 지원하지 않는 환경의 자체 재검증을 “독립 검증 완료”로 표시하지 않는다. |
| 강제 차단 | plugin manifest의 `PreToolUse`, `aml-guard.sh`의 `tool_input`·종료 코드 | Codex 도구 입력·훅 계약과 배포 환경을 별도 확인. 지침만 옮긴 상태를 기존 훅과 동등한 강제 차단이라고 설명하지 않는다. |
| 사용량 수집 | `observe.py:81,128`의 `~/.claude/projects`·assistant usage | Codex 세션 수집기를 별도로 검증. Claude 기록으로 Codex 작업 비용을 계산하지 않는다. 수집이 불가능하면 미수집으로 표시하되 작업 결과·검증 기록은 계속 남긴다. |
| 설치 | `install.sh:12,44`의 Claude 경로와 복사 대상 | Codex 전용 설치·업데이트 안내 추가. 기존 설치 기본 동작을 보존하고 사용자 절대 경로를 하드코딩하지 않는다. |

공식 이식 안내도 `commands/`와 `agents/`의 재사용 가능한 동작을 스킬로 전환하도록 안내한다. 로컬 스킬 탐색 위치인 `.agents/skills`와 배포용 플러그인 내부 `skills/`는 용도가 다르다. [공식 이식 안내](https://developers.openai.com/plugins/guides/submit-claude-plugin), [스킬 문서](https://learn.chatgpt.com/docs/build-skills)

Codex의 프로젝트 지침은 `AGENTS.md` 체계로 제공한다. 프로젝트 전체에 동일 파일을 무조건 새로 만드는 대신 기존 지침과 적용 범위를 존중해야 한다. [AGENTS.md 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

현재 공식 패키징 안내상 lifecycle hook은 수동 설치한 Codex desktop 플러그인에 지원되며 공개 디렉터리 제출에는 제한이 있다. 따라서 “Codex에는 훅이 없다”도, “모든 Codex에서 Claude 훅을 그대로 쓴다”도 적절하지 않다. 지원할 실행 환경과 배포 경로를 먼저 정해야 한다. [훅 배포 제약](https://developers.openai.com/plugins/build/plugins)

## 업데이트할 문서와 설정

| 우선순위 | 파일 | 수정 내용 |
|---|---|---|
| 필수 | 루트 `README.md` | 두 플랫폼 지원 소개, 설치 안내 분기, 7개 기능 대응표, 새 폴더 지도, 차이·제약 링크. |
| 필수 | `aml/README.md` | Claude 전용 안내임을 명시. 공통 원칙은 공통 문서 링크로 연결. Codex 지원과 혼동되는 보편적 기능 약속 정리. |
| 신규 | `codex/README.md` | 지원하는 Codex 실행 환경·설치 형식·7개 스킬 호출·업데이트·제거·제약·문제 해결. 호출 표기는 실제 설치 후 확인. |
| 필수 | 루트 README의 호환성 표 + `codex/README.md` | 공통 기능 대응표는 루트에, Codex의 제약·미구현 상세는 Codex 안내에 둔다. |
| 필수 | `aml/commands/` 7개 + 신규 Codex 스킬 | 목적·산출물은 대응시키고 안내 파일·규칙 경로·도구·호출 문법은 플랫폼별로 작성. 명령마다 본문 전체를 단순 복제하지 않도록 공통 절차 추출. |
| 필수 | `aml/templates/claude.template.md` + 신규 `agents.template.md` | 공통 항목 구조는 맞추되 각 플랫폼의 프로젝트 안내 파일로 생성. 기존 파일 보존. |
| 필수 | `spec.template.md`, `progress.template.md`, `skill.template.md` | 주석·예시에 남은 `.claude/skills`, `CLAUDE.md`, Claude 지칭을 공통 설명 또는 플랫폼별 값으로 변경. |
| 검토 | `task.template.md`, `intent.template.md`, `review.template.md` | 공통 재사용 후보. 명령과 링크에 플랫폼 의존성이 없는지 확인 후 동일 원본 사용. |
| 필수 | `aml/references/artifact-chain.md` | 프로젝트 지침을 `CLAUDE.md`/`AGENTS.md`로 매핑하고 공통 산출물 연결 설명. |
| 필수 | `aml/references/autonomy-and-guardrails.md` | 공통 행동 원칙과 플랫폼별 강제 차단 설정을 분리. Codex에서 검증하지 않은 보장을 쓰지 않음. |
| 필수 | `aml/references/next-steps.md` | `claude`, `claude -p`, Claude Actions·설정·모니터링 안내를 Claude 전용으로 표시. Codex 대응은 검증된 것만 추가. |
| 필수 | `aml/Example.md` + Codex 예시 | 실제 호출부터 생성 파일·기록·검증까지 두 환경의 차이를 보여 줌. 측정 불가 사례도 설명. |
| 신규 | `claude-code/README.md`, `codex/docs/development.md` | 각 플랫폼의 테스트·패키징·릴리스 방법. 공통 산출물을 바꿀 때 양쪽 반영 및 호환성 확인 원칙. |
| 설정 | 기존 manifest·marketplace, 신규 Codex manifest | 플랫폼별 설명·버전·경로 일치. Codex marketplace 등록 방식은 배포 경로 확정 후 결정. |
| 설치 | `claude-code/install.sh`, Codex 설치 안내 | 기존 설치 결과는 보존하되 저장소에서의 실행 경로 변경을 안내. Codex 설치 스크립트는 실제 배포 방식에 필요할 때만 추가. |

위 표의 `aml/...`은 현재 파일 위치를 뜻한다. 이동 후 Claude 문서의 실제 경로는 `claude-code/aml/...`이다. `claude-code/README.md`는 설치·개발 안내, `claude-code/aml/README.md`는 설치 패키지에 포함되는 사용자 설명으로 역할을 구분해 중복을 줄인다.

## 기능 범위와 위험

**보통 먼저 정할 것은 지원 환경, 기능 동등성, 공통 문서의 원본 위치다.** 이번 분석의 추천은 아래와 같다. 아직 사용자 확정 사항은 아니다.

- 7개 사용자 워크플로우를 모두 Codex에 제공한다. 기존 캐시처럼 4개만 제공하면 review/next/rule의 기능 공백을 설명해야 한다.
- `spec.md`, `task.md`, `progress.md`, `intent.md`, `REVIEW.md` 형식은 공통으로 유지한다. 플랫폼을 바꿔도 작업을 이어갈 수 있게 한다.
- 토큰·비용 측정과 강제 차단의 완전 동등성은 별도 단계로 검증한다. 초기 미지원 항목은 문서와 doctor에서 명시한다. 이 범위는 구현 전에 확정해야 한다.
- 동일 프로젝트에서 두 도구가 동시에 `task.md`·`progress.md`를 수정하면 덮어쓰기·체크 상태 충돌이 생길 수 있다. 첫 버전은 순차 전환을 기준으로 하고 동시 작업 보장은 제외하는 편이 단순하다.
- 두 패키지를 수동으로 각각 고치면 규칙이 갈라질 수 있다. 공통 산출물의 필수 항목과 양쪽 반영 절차를 정하고 호환성 검증으로 관리한다. 처음부터 루트 shared 폴더나 생성기를 추가하지 않는다.
- 이름이 같은 캐시 버전과 새 설치를 함께 활성화하면 어떤 스킬이 선택됐는지 혼동할 수 있다. 업데이트·중복 설치 확인을 Codex 안내에 포함한다.

## 이후 작업 순서와 검증 기준

1. Codex 지원 환경과 배포 방식, 훅·독립 검증·측정의 첫 버전 범위를 결정한다.
2. 공통 산출물 형식과 플랫폼별 경로 표를 확정한다.
3. Claude의 설치 스크립트·marketplace·패키지·테스트를 함께 `claude-code/`로 이동하고, 설치 결과와 두 smoke test를 확인한다. 이 단계는 기능 변경 없이 진행해 문제 원인을 구분한다.
4. 별도 단계에서 `codex/aml/`에 7개 스킬과 필요한 템플릿을 추가한다.
5. 독립 검증·안전망·측정은 지원 범위에 맞게 연결하고, 미지원 상태도 명확하게 보고한다.
6. 설치 문서·사용 예시·호환성 표·개발 가이드를 맞춘다.
7. 새 경로에 설치한 패키지에서도 모든 리소스가 열리는지, 7개 기능이 인식되는지 확인한다. 기존 Claude guard/observe smoke test와 Codex 시나리오 검증을 수행한다.

사용자가 직접 확인할 기준은 “두 도구에서 동일 프로젝트의 문서를 이어 읽을 수 있음”, “기존 지침 파일을 덮어쓰지 않음”, “실제 지원하지 않는 측정·검증·차단을 성공으로 보고하지 않음”, “기존 Claude 설치와 명령이 유지됨”이다.

이번 재검토에서는 이 조사 문서만 수정했다. 폴더 이동, 설치·코드·스킬·manifest 변경, 테스트 실행, `spec.md`/`task.md`/`progress.md` 생성은 하지 않았다. 공식 자료는 앞선 조사에서 확인했으며 실제 Codex 설치·호출·훅 동작의 호환성 시험은 후속 작업이다.
