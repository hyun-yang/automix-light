---
description: 시작 전 점검 — 파일 3개와 완성 기준, git/python3, Langfuse 설정을 확인한다. 읽기 전용.
allowed-tools: Read, Bash, Glob, Grep
---

# /aml:doctor — 시작 전 점검

프로젝트 루트에서 아래를 순서대로 점검하고, spec.md 가 있으면 그 언어로(없으면 사용자 대화 언어로) 쉽게 보고한다. 아무것도 고치지 않는다.

## 막는 것 — 걸리면 ❌ 와 고치는 법을 보고

1. spec.md / task.md / progress.md 가 셋 다 있는가 → 없으면: "/aml:new 로 시작하세요"
2. spec.md 의 "완성 기준"에 체크박스(`- [ ]` 또는 `- [x]`)가 1개 이상 있는가
3. task.md 에 태스크 체크박스가 1개 이상 있는가

## 안내만 — 진행을 막지 않고 ⚠️ 로 보고

4. git 저장소인가 (`git rev-parse --is-inside-work-tree`) — 아니면: "git 이 없어도 되지만, 있으면 실수를 되돌리기 쉬워요"
5. python3 이 있는가 (`command -v python3`) — 없으면: "측정 줄(모델·시간·토큰·비용)이 progress.md 에 기록되지 않아요"
6. Langfuse 상태 — 셋 중 하나로 보고. **Langfuse 는 어떤 경우에도 진행을 막지 않는다.**
   - `.aml/config.yaml` 이 없거나 `langfuse:` 값이 "on" 이 아니면 → "Langfuse 전송: 꺼짐(기본값)". 켜는 법은 README 의 "Langfuse 켜기" 절.
   - "on" 인데 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY 환경변수가 없으면 → ⚠️ "켜져 있지만 키가 없어 전송이 생략됩니다" + 키 설정법(키 값은 절대 출력하지 않는다 — 있/없음만).
   - "on" 이고 키가 있으면 → `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/observe.py" ping` 으로 연결 확인, OK/WARN 을 그대로 보고.

## 보고 형식

항목마다 ✅/❌/⚠️ 한 줄. 마지막에 다음 행동 한 줄 — 파일이 없으면 /aml:new, 미완료 태스크가 있으면 /aml:go, 문제가 없으면 "바로 시작해도 됩니다".
