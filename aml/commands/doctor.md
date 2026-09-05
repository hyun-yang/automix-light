---
description: 시작 전 점검 — 파일 3개와 완성 기준, git/python3, Langfuse 설정을 확인한다. 읽기 전용.
allowed-tools: Read, Bash, Glob, Grep
---

# /aml:doctor — 시작 전 점검

프로젝트 루트에서 아래를 순서대로 확인하고 한국어로 쉽게 보고한다. 아무것도 고치지 않는다.

## 막는 항목 — 실패하면 ❌ 와 해결 방법을 알린다

1. spec.md / task.md / progress.md 가 모두 있는가? → 없으면: "/aml:new 부터 하세요"
2. spec.md 의 "완성 기준"에 체크박스(`- [ ]` 또는 `- [x]`)가 하나 이상 있는가?
3. task.md 에 할 일 체크박스가 하나 이상 있는가?

## 참고만 하는 항목 — 막지 않고 ⚠️ 로 알린다

4. CLAUDE.md 가 있는가? — 없으면: "이 프로젝트가 뭔지 Claude 가 매번 다시 파악해야 합니다. /aml:new 를 실행하면 만들어 드립니다"
5. git 저장소인가(`git rev-parse --is-inside-work-tree`)? — 아니면: "/aml:new 가 git 을 준비하고 기본 브랜치를 main 으로 맞춰 줍니다 — 있으면 실수를 되돌리기 쉽습니다"
6. python3 를 쓸 수 있는가(`command -v python3`)? — 아니면: "progress.md 에 측정 줄(모델·시간·토큰·비용)이 남지 않습니다"
7. Langfuse 상태 — 셋 중 하나로 보고한다. **Langfuse 는 어떤 경우에도 막지 않는다.**
   - `.aml/config.yaml` 이 없거나 `langfuse:` 가 "on" 이 아니면 → "Langfuse 전송: 꺼짐(기본값)". 켜는 방법은 README 의 "Langfuse 켜기" 항목.
   - "on" 인데 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY 환경변수가 없으면 → ⚠️ "켜져 있지만 키가 없어 전송을 건너뜁니다" + 키 설정 방법 (키 값은 절대 출력하지 않는다 — 있음/없음만).
   - "on" 이고 키도 있으면 → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/observe.py" ping` 으로 연결을 확인하고, 나온 정상/경고 결과를 그대로 전한다.

## 보고 형식

항목마다 ✅/❌/⚠️ 한 줄씩. 마지막에 다음에 할 일을 한 줄로 — 파일이 없으면 /aml:new, 할 일이 남았으면 /aml:go, 문제가 없으면 "바로 시작하셔도 됩니다".
