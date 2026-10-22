# 도움말 추가 계획 — 개발 과정에서 무엇이 남나요?

상태: 2026-10-22 `$aml:go` 요청으로 두 HTML 매뉴얼의 도움말에 반영했다. 아래는 기획 당시의 문안과 확인 계획이며, 실제 확인 결과는 [확인 기록](verification.md)에서 볼 수 있다.

## 정한 방향

- 한글판과 영문판의 도움말 서랍에 질문 하나씩 추가한다. 본문에서 처음부터 배우는 명령은 계속 new·go·next까지다.
- 사용자가 고른 예외: review·rule은 이 접힌 표에서만 선택 기능으로 소개한다.
- 보내 준 APG 표를 AML에 맞춰 옮긴다. 일곱 단계·네 열을 유지하고 설명은 짧게 쓴다.
- 두 표 모두 Codex 표기를 쓴다. Claude Code·Copilot CLI 표기는 기존 “다른 도구” 도움말로 연결한다.

## 한글판 문안

**질문: 만드는 과정은 어떤 단계로 진행되고, 무엇이 남나요? (SDLC)**

**답:** 소프트웨어 개발 생명 주기(SDLC)는 아이디어를 계획하고, 만들고, 확인하고, 고쳐 나가는 전체 과정이에요. automix-light가 각 단계에서 남기는 내용을 아래에 정리했어요.

**시작은 여전히 new·go 두 개면 충분해요.** go에 확인과 검토가 포함되어 있어요. 아래 review·rule은 필요할 때만 쓰는 선택 기능이니 지금 외울 필요는 없어요.

| 만드는 단계 | AML 명령 | 남는 것 | 담긴 내용 |
|---|---|---|---|
| 계획하기 | `$aml:new` | `intent.md` | 왜 만들고 싶은지, 처음 말한 그대로 |
| 필요한 것 정하기 | `$aml:new` | `spec.md` | 필요한 기능·선택한 것·참고 자료·걱정·완성 기준 |
| 모습과 순서 정하기 | `$aml:new` | `task.md`, 화면 시안, `AGENTS.md` 등¹ | 할 일 순서와 바뀌는 파일·위험·확인 방법, 프로젝트 안내와 규칙 |
| 만들기 | `$aml:go` | 코드, 저장 기록(커밋), `progress.md` | Git 저장소라면 작업별 저장 기록, 무엇을 왜 바꿨는지 |
| 잘 되는지 확인하기 | `$aml:go` | 확인 표시가 된 `spec.md`의 완성 기준 | 실제로 실행해 확인한 결과² |
| 다시 살펴보기 | `$aml:go` · `$aml:review`(선택) | `REVIEW.md` 기준에 따른 결과를 `progress.md`에 기록 | 안 되는 곳·정보 보호·약속대로 만들었는지 |
| 써 보고 개선하기 | `$aml:next` · `$aml:rule`(선택) | 새 할 일, 새 `intent.md` 항목, 규칙 카드 또는 안내 파일의 규칙 | 써 본 느낌을 다음 일로, 반복 실수는 예방 규칙으로 |

¹ `AGENTS.md`는 작업 도구가 읽는 프로젝트 안내예요. Claude Code에서는 `CLAUDE.md`를 써요. 이런 안내 파일은 없을 때 준비하며, 매번 새로 만들지는 않아요. 화면 시안은 모습 비교가 필요할 때 만들어요.

² Codex는 기본적으로 작업한 AI가 다시 확인해요(자체 확인). 별도 도우미에게 실제로 맡겼을 때만 독립 확인이라고 기록해요. 확인한 것과 못 한 것은 진행 기록에서 함께 살펴보세요. 도구별 자세한 차이는 기존 “자체 확인과 독립 확인” 도움말로 연결해요.

명령 앞의 `$`는 Codex 표기예요. Claude Code·Copilot CLI에서는 `/aml:new`처럼 시작해요. 정확한 표기는 기존 “다른 도구” 도움말로 연결해요.

설명 보완: 코드·파일·화면 시안·검증·리뷰·git·커밋·SDLC는 기존 용어집의 쉬운 설명으로 연결한다. “완성 기준”은 “다 됐다고 확인할 항목”, “규칙 카드”는 “반복 실수를 막는 약속을 적은 문서”라는 짧은 뜻을 표 아래에 덧붙인다.

## 영문판 문안

**Question: How do automix-light's outputs fit the software development life cycle (SDLC)?**

**Answer:** The software development life cycle is the process of planning, building, checking, and improving software. Here's what automix-light keeps along the way.

**You still only need new and go to start.** go includes checking and reviewing. review and rule below are optional helpers; you don't need to learn them now.

| Phase | AML command | Output | What it holds |
|---|---|---|---|
| Planning | `$aml:new` | `intent.md` | Why you want to build it, in your own words |
| Requirements | `$aml:new` | `spec.md` | Features, decisions, references, concerns, and completion criteria |
| Design | `$aml:new` | `task.md`, screen mockups, `AGENTS.md`, as needed¹ | Work order, files to change, risks, and checks; project guidance and rules |
| Implementation | `$aml:go` | Code, commits, `progress.md` | In a Git repository, a commit per task; what changed and why |
| Testing / Verification | `$aml:go` | Checked completion criteria in `spec.md` | Results confirmed by actually running things² |
| Review | `$aml:go` · `$aml:review` (optional) | Findings in `progress.md`, using `REVIEW.md` as the checklist | Bugs, protection of information, and whether promises were kept |
| Maintenance / Next iteration | `$aml:next` · `$aml:rule` (optional) | New tasks, a new `intent.md` entry, rules in a rule card or project guide | Feedback becomes the next task; repeated mistakes become prevention rules |

¹ `AGENTS.md` is a project guide for the tool. Claude Code uses `CLAUDE.md`. Guidance files are prepared if missing, rather than recreated every time. Mockups are made when comparing screen designs would help.

² Codex defaults to a self-check by the AI that did the work. A check is recorded as independent only when it was actually assigned to a separate helper. Read the progress notes to see what was checked and what couldn't be checked. See the self-check / independent check help section for the tool differences.

The `$` prefix is for Codex. Claude Code and Copilot CLI use commands such as `/aml:new`. See the existing command table for the exact forms.

영문 용어 설명도 기존 용어집으로 연결한다. “completion criteria”는 “the things to check before calling it done”, “rule card”는 “a document of agreements that help prevent repeated mistakes”로 짧게 풀어 쓴다.

## 제작할 때 확인할 것

- 위치: 두 언어의 도움말 서랍에 같은 내용을 추가한다. 기본은 접힌 상태다.

- 표 위의 시작 안내와 선택 기능 표시를 먼저 읽을 수 있게 한다. 표의 단계별 행이 각각 별도 명령을 외우라는 뜻으로 보이지 않도록 한다.
- 새 도움말 하나를 추가하면 전체 details 개수는 6개에서 7개가 된다. 기존 임시 검사에서 정확히 6개라고 가정한 곳은 새 요구에 맞게 조정한다. 사용 동작을 확인하는 검사는 유지한다.
- 표의 열 제목과 단계 이름에 표 머리글 표시를 한다. 360px에서 네 열을 억지로 좁히지 않는다. 필요하면 표 영역에만 좌우 이동을 허용하고, 이동 안내·키보드 초점·읽기 이름을 제공한다.
- 360·768·1280px에서 두 언어를 직접 열어 보고 글자 잘림, 설명과 표의 대응, 도움말 열고 닫기, 언어 전환, 오프라인 사용을 확인한다.
- 추가 명령이 없는 기존 검사 전제는 “기본 흐름은 세 종류, 접힌 표의 선택 기능은 review·rule”로 고친다. 실제 명령 표기의 정확성은 계속 검사한다.
- AGENTS.md의 기존 검사와 REVIEW.md의 버그·안전·약속 지킴 검토를 수행하고 manual/verification.md에 근거를 남긴다.
