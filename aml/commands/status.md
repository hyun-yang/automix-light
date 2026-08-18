---
description: spec.md / task.md / progress.md 를 바탕으로 진행 상황을 쉬운 말로 요약한다. 읽기 전용.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# /aml:status — 진행 상황 확인

프로젝트 루트의 spec.md, task.md, progress.md 를 읽고 요약한다. 셋 다 없으면 /aml:new 부터 하라고 알린다.

보고(한국어로, 쉬운 말로):

- **어디까지 왔나** — 끝난/남은 할 일 개수, 가장 최근 작업 한 줄
- **막힌 것** — progress.md 에 막힌 것이 적혀 있으면 그 내용과 사용자가 답해 줘야 할 질문
- **다음에 할 일** — 할 일이 남았으면 /aml:go, 다 끝났으면 다음 기능을 위해 /aml:new

마지막에 제안을 덧붙인다 — 원하면 **퀴즈**: 지금까지 만든 것에 대한 쉬운 질문 3개쯤으로, 사용자가 다른 사람에게 설명할 수 있는지 확인한다. 흐름을 놓치지 않는다는 건 코드를 읽는 게 아니라 이해했는지 확인하는 것이다.
