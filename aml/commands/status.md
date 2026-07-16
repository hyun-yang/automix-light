---
description: spec.md / task.md / progress.md 기반으로 진행 상황을 쉬운 말로 요약한다. 읽기 전용.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# /aml:status — 진행 확인

프로젝트 루트의 spec.md, task.md, progress.md를 읽고 요약한다. 셋 다 없으면 /aml:new 부터 하도록 안내한다.

보고 내용 (쉬운 말로):

- **어디까지 왔나** — 완료/남은 태스크 수, 최근에 한 일 한 줄
- **막힌 것** — progress.md에 막힘 기록이 있으면 그 내용과 사용자가 답해줘야 할 질문
- **다음 행동** — 남은 태스크가 있으면 /aml:go, 다 끝났으면 /aml:new 로 다음 기능

마지막에 제안한다 — 원하면 **퀴즈**: 지금까지 만든 것에 대해 쉬운 퀴즈 3문제 정도를 내서, 사용자가 만든 것을 남에게 설명할 수 있는 상태인지 확인한다. 루프 안에 머무는 법은 코드 읽기가 아니라 이해 확인이다.
