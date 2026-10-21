# 측정 — Copilot 판 측정 줄은 어떻게 만들어지나

/aml:go 는 할 일마다 `progress.md` 에 측정 줄을 하나 남깁니다. 숫자는 `scripts/observe.py` 가 Copilot CLI 의 세션 기록을 읽어 만듭니다. 측정은 **작업을 막지 않습니다** — 어떤 이유로든 확실하지 않으면 숫자를 지어내지 않고 `측정: 기록 없음 (이유)` 를 남깁니다.

```text
측정: gpt-6-luna · 3분 27초 · 토큰 입력 6 / 출력 189 (캐시 읽기 24.8k / 쓰기 6.0k) · 비용 미산정 · AI 크레딧 0.11
```

## 부르는 법

**Python 실행 명령 선택:** `python3 -c "import sys; print(sys.version_info[0])"` → `python -c "import sys; print(sys.version_info[0])"` → `py -3 -c "import sys; print(sys.version_info[0])"` 순서로 실제 실행한다. 출력이 `3`이고 종료 코드가 0인 첫 명령을 고른다. 아래의 `<파이썬>`은 고른 명령(`python3`, `python`, `py -3`)으로 바꾸어 실행한다. Windows의 Microsoft Store 바로가기는 이름이 있어도 실행에 실패할 수 있다.


```bash
<파이썬> "<패키지>/scripts/observe.py" task-start --label "1.2 카드 추가 창"
#  → 시작: 2026-10-19T18:00:00+10:00      (이 시각을 아래 --since 에 씀)
<파이썬> "<패키지>/scripts/observe.py" task-done --since 2026-10-19T18:00:00+10:00 --label "1.2 카드 추가 창"
<파이썬> "<패키지>/scripts/observe.py" summary progress.md     # /aml:status
<파이썬> "<패키지>/scripts/observe.py" check                   # /aml:doctor
```

`<패키지>` 는 스킬 파일(SKILL.md)이 있는 폴더의 두 단계 위입니다.

## 어느 세션을 읽나

- Copilot 이 셸 명령을 실행할 때 넘겨주는 세션 번호(`COPILOT_AGENT_SESSION_ID`)로 **지금 세션 하나만** 고릅니다. `--session <번호>` 로 직접 줄 수도 있습니다.
- 기록 파일은 `$COPILOT_HOME/session-state/<세션 번호>/events.jsonl`(기본 `~/.copilot/session-state/…`)입니다. 파일 안 `session.start` 의 번호가 같아야 읽습니다.
- 세션 번호를 모르면 **같은 폴더에서 연 다른 세션을 대신 고르지 않습니다.** 같은 프로젝트에서 연 다른 작업이 섞이기 때문입니다. 이때는 `기록 없음` 입니다.
- 세션 기록에는 대화 내용도 들어 있지만, 이 스크립트는 사용량 숫자만 읽고 어디에도 보내지 않습니다.

## 구간은 어떻게 자르나

- Copilot 은 모델을 부를 때마다 **그 한 번에 쓴 양**을 `session.usage_record` 줄로 남깁니다. 구간 사용량 = 시작 시각 뒤, 지금까지의 `session.usage_record` 를 모두 더한 값입니다.
- 같은 기록(같은 `usageId`)이 두 번 있으면 한 번만 셉니다.
- 할 일 도중에 세션을 새로 열었다면(세션 시작 시각이 할 일 시작보다 나중) 앞 세션에서 쓴 양을 알 수 없으니 **이어 붙이지 않고** `기록 없음` 입니다.
- 모델은 기록마다 적힌 `model` 로 정합니다. 구간 안에서 모델이 바뀌면 모델별로 나눠 적습니다. Copilot 의 "auto" 모드는 기록에 실제로 쓴 모델 이름이 남습니다.

## 토큰 숫자의 관계 (두 번 세지 않기)

2026-10-19 에 Copilot CLI 1.0.98 의 실제 기록 7개로 확인했습니다 — 7개 모두 아래 관계를 정확히 지켰고, 측정 줄의 숫자가 Copilot 화면 끝에 나오는 `Tokens ↑ … (… cached, … written) • ↓ …` · `AI Credits …` 와 같았습니다.

| 기록의 이름 | 뜻 | 관계 |
|---|---|---|
| `inputTokens` | 입력 전체 | 캐시 읽기와 캐시 쓰기가 **안에 들어 있음** |
| `cacheReadTokens` | 그중 캐시에서 읽은 입력 | |
| `cacheWriteTokens` | 그중 캐시에 새로 쓴 입력 | |
| `copilotUsage.tokenDetails` 의 `input` | 캐시 안 된 입력 | `inputTokens − cacheReadTokens − cacheWriteTokens` 와 같음 |
| `outputTokens` | 출력 전체 | |
| `reasoningTokens` | 그중 추론 | `outputTokens` 이하 |
| `copilotUsage.totalNanoAiu` | Copilot 이 계산한 사용량 | 10억으로 나누면 화면의 AI 크레딧 |

측정 줄의 **"입력"은 캐시 안 된 입력**, **"캐시 읽기 / 쓰기"는 따로** 적습니다. Claude 판 측정 줄과 같은 뜻이 되도록 맞춘 것이라, 세 도구의 줄이 섞여도 요약에서 같은 칸끼리 더해집니다. 위 관계가 하나라도 맞지 않으면 추측하지 않고 `기록 없음` 입니다.

## 비용과 AI 크레딧

- **달러 비용**은 단가와 토큰의 뜻을 확인한 모델만 계산합니다. 지금은 확인한 단가가 없어서 Copilot 판 측정 줄은 모두 `비용 미산정` 입니다. Copilot 구독으로 쓰면 토큰마다 돈이 나가지 않기도 합니다. 모르는 모델의 비용은 **0 으로 적지 않습니다** — 0 은 "공짜"로 읽히기 때문입니다.
- **AI 크레딧**은 Copilot 이 기록에 직접 남긴 사용량을 그대로 옮긴 것입니다(어림값이 아님). 달러와 단위가 달라 합치지 않고 따로 적습니다. 구간 안에 크레딧이 없는 기록이 하나라도 있으면 그 줄에는 크레딧을 적지 않습니다.

| 모델 | 입력 | 캐시 입력 | 출력 | 출처 | 확인일 |
|---|---|---|---|---|---|
| (아직 없음) | | | | | |

단가를 넣을 때는 공식 가격표에서 확인하고, 이 표와 `observe.py` 의 `PRICING` 을 함께 고칩니다.

## 요약 (/aml:status)

`summary` 는 `progress.md` 의 측정 줄을 모두 읽어 작업 수 · 걸린 시간 합 · 토큰(대략) · 알려진 달러 비용 합 · AI 크레딧 합을 보여 줍니다. 측정 줄의 토큰은 `12.3k` 처럼 반올림된 표기라 합계도 **대략**입니다. 비용을 모르는 작업 수와 측정 없는 작업 수는 따로 셉니다. Claude 판·Codex 판 줄이 섞여 있어도 됩니다.

## 알려진 한계

- Copilot CLI **1.0.98 이상**의 기록(`session.start` · `session.usage_record`)만 읽습니다. 그보다 옛 버전, 버전을 알 수 없는 기록은 `기록 없음` 입니다.
- 확인 도우미(verifier) 같은 하위 에이전트의 사용량이 같은 세션 기록에 함께 남는지는 아직 확인하지 않았습니다. 따로 남는다면 그만큼 측정 줄에서 빠집니다.
- Langfuse 전송은 Copilot 판 첫 버전에 없습니다.
