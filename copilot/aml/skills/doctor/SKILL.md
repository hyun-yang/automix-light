---
name: doctor
description: 시작 전 점검 — 계획 파일과 완성 기준, 프로젝트 안내(AGENTS.md), 도구 전환 준비, 안전망 안내, git/python3 를 확인한다. 읽기 전용. "점검해 줘", "준비됐어?", "/aml:doctor" 일 때 쓴다.
---

# /aml:doctor — 시작 전 점검

**Python 실행 명령 선택:** `python3 -c "import sys; print(sys.version_info[0])"` → `python -c "import sys; print(sys.version_info[0])"` → `py -3 -c "import sys; print(sys.version_info[0])"` 순서로 실제 실행한다. 출력이 `3`이고 종료 코드가 0인 첫 명령을 고른다. 아래의 `<파이썬>`은 고른 명령(`python3`, `python`, `py -3`)으로 바꾸어 실행한다. Windows의 Microsoft Store 바로가기는 이름이 있어도 실행에 실패할 수 있다.


프로젝트 루트에서 아래를 순서대로 확인하고 한국어로 쉽게 보고한다. **아무것도 고치지 않는다** — 파일을 만들거나 바꾸거나 지우지 않는다. 고칠 것이 보이면 방법만 알려 준다.

## 막는 항목 — 실패하면 ❌ 와 해결 방법을 알린다

1. spec.md / task.md / progress.md 가 모두 있는가? → 없으면: "/aml:new 부터 하세요"
2. spec.md 의 "완성 기준"에 체크박스(`- [ ]` 또는 `- [x]`)가 하나 이상 있는가?
3. task.md 에 할 일 체크박스가 하나 이상 있는가?

## 참고만 하는 항목 — 막지 않고 ⚠️ 로 알린다

4. **AGENTS.md** 가 있는가? — 셋 중 하나로 보고한다.
   - 있으면 ✅. 120줄이 넘으면 ⚠️ "한 페이지를 넘었습니다. 이제 안 맞는 줄이 있는지 /aml:rule 로 정리해 보세요".
   - 없는데 **CLAUDE.md 가 있으면** ⚠️ "Claude Code 에서 시작한 프로젝트로 보입니다. Copilot 은 CLAUDE.md 도 읽지만, aml Copilot 판은 AGENTS.md 를 안내 파일로 씁니다 — [도구 전환 준비](../../references/switching.md) 절차대로 AGENTS.md 만 만들면 기존 계획을 그대로 이어서 쓸 수 있습니다. 새로 기획하지 마세요."
   - 둘 다 없으면 ⚠️ "이 프로젝트가 뭔지 Copilot 이 매번 다시 파악해야 합니다. /aml:new 를 실행하면 만들어 드립니다".
5. **intent.md** 가 있는가? — 없으면: "왜 만들기로 했는지 기록이 없습니다. 다음에 /aml:new 나 /aml:next 를 실행하면 만들어집니다" (지금 당장은 문제없다).
6. **REVIEW.md** 가 있는가? — 없으면: "리뷰 기준표가 없습니다. /aml:review 를 처음 실행하면 만들어 드립니다".
7. **`.aml/FIXING`** 이 남아 있는가? — 있으면 ⚠️: "버그를 고치는 중이라는 표시가 남아 있습니다. 고치는 동안에는 테스트 파일을 고치지 않기로 한 약속입니다(그동안 테스트 파일을 고치려 하면 aml 안전망 훅이 막습니다). 다 끝난 상태라면 `rm .aml/FIXING` 으로 지우세요."
8. **안전망** — 항상 이 문장 그대로 ⚠️ 로 알린다:
   "aml 플러그인이 켜져 있으면 안전망 훅도 함께 켜져, 비밀키(.env) 커밋 · 고치는 중 테스트 파일 변경 · 강제 푸시·하드 리셋을 막습니다. 켜졌는지는 Copilot 대화에서 `/env` 를 쳐서 Hooks 칸에 `preToolUse … (sources: aml)` 이 보이는지로 확인하세요. 훅이 시간을 넘기면 Copilot 이 막지 않고 그냥 통과시키니, 되돌리기 어려운 일은 사람도 한 번 더 봐 주세요."
   이 스킬 안에서 `/env` 결과를 직접 보지 못했다면 "켜져 있다"고 단정하지 않는다.
9. **git** 저장소인가(`git rev-parse --is-inside-work-tree`)? — 아니면: "/aml:new 가 git 을 준비하고 기본 브랜치를 main 으로 맞춰 줍니다 — 있으면 실수를 되돌리기 쉽습니다"
10. **Python 3**를 실제로 실행할 수 있는가(위 선택 절차)? — 아니면: "progress.md 에 측정 줄(모델·시간·토큰·비용)이 남지 않습니다. 작업은 그대로 진행됩니다"
11. **규칙 카드** — `.agents/skills/*/SKILL.md` 개수를 세어 알린다(0개도 정상). 있으면 이름만 한 줄로. `.claude/skills/` 에만 카드가 있으면 ⚠️ "Claude Code 용 규칙 카드입니다. Copilot 도 읽으니 그대로 두면 됩니다. 새 규칙은 /aml:rule 이 `.agents/skills/` 에 만듭니다."
12. **설정을 바꾼 뒤 확인했는가** — AGENTS.md · REVIEW.md · 규칙 카드 중 가장 최근에 고쳐진 시각이 progress.md 의 마지막 기록보다 나중이면 ⚠️: "Copilot 을 이끄는 설정이 바뀐 뒤 아직 전체 확인을 안 했습니다. /aml:go 나 /aml:review 로 완성 기준을 한 번 다시 훑어보세요."
13. **사용량 측정** — `<파이썬> "<패키지>/scripts/observe.py" check` 를 돌려 나온 한 줄을 그대로 전한다(`<패키지>` 는 이 SKILL.md 의 두 단계 위). 측정을 못 해도 막지 않는다. Langfuse 전송은 Copilot 판 첫 버전에 없다고 한 줄로 알린다.

## 보고 형식

항목마다 ✅/❌/⚠️ 한 줄씩. 마지막에 다음에 할 일을 한 줄로 — 파일이 없으면 /aml:new, AGENTS.md 만 없으면 도구 전환 준비, 할 일이 남았으면 /aml:go, 다 끝났으면 /aml:next, 문제가 없으면 "바로 시작하셔도 됩니다".
