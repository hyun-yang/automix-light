# install.ps1 — automix-light 마켓플레이스를 고정된 경로에 복사하고,
# Claude Code 안에서 실행할 /plugin 명령을 출력한다. (Windows PowerShell 판 — install.sh 와 같은 일)
#
# 사용법 (저장소 루트에서, PowerShell):
#   PS> cd automix-light
#   PS> powershell -ExecutionPolicy Bypass -File claude-code\install.ps1
#
# 이 파일은 BOM 이 붙은 UTF-8 로 저장한다 — 그래야 Windows 기본 PowerShell(5.1)이 한글을 바르게 읽는다.

$ErrorActionPreference = 'Stop'

# 출력이 파일이나 다른 프로그램으로 넘어갈 때도 한글이 깨지지 않게
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$ScriptDir = $PSScriptRoot
$Target = $env:AUTOMIX_LIGHT_MARKETPLACE_DIR
if (-not $Target) {
  $Target = Join-Path $HOME '.claude-marketplaces\automix-light'
}

Write-Output "automix-light 설치 도구"
Write-Output "─────────────────────────────────────────────────"
Write-Output "원본: $ScriptDir"
Write-Output "대상: $Target"
Write-Output ""

# 1. 여기가 마켓플레이스 루트인지 확인
$Marketplace = Join-Path $ScriptDir '.claude-plugin\marketplace.json'
if (-not (Test-Path -LiteralPath $Marketplace -PathType Leaf)) {
  [Console]::Error.WriteLine("오류: $Marketplace 이 없습니다.")
  [Console]::Error.WriteLine("      저장소의 claude-code\install.ps1 을 그대로 실행하세요 (예: powershell -ExecutionPolicy Bypass -File claude-code\install.ps1).")
  exit 1
}

# 2. JSON 파일 검사 — PowerShell 기본 기능으로 하므로 파이썬이 필요 없다.
#    한글이 들어 있으므로 UTF-8 로 읽는다.
foreach ($pair in @(
    @($Marketplace, 'marketplace.json'),
    @((Join-Path $ScriptDir 'aml\.claude-plugin\plugin.json'), 'plugin.json'))) {
  try {
    Get-Content -LiteralPath $pair[0] -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
  } catch {
    [Console]::Error.WriteLine("오류: $($pair[1]) 이 올바른 JSON 이 아닙니다")
    exit 1
  }
}

# 3. 고정 경로로 복사 (기존 설치본은 백업)
#    마켓플레이스에 필요한 것만 옮긴다 — .git/.venv/.idea 는 복사하지 않는다.
$Parent = Split-Path -Parent $Target
if ($Parent) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
if (Test-Path -LiteralPath $Target -PathType Container) {
  $Backup = "$Target.bak"
  Write-Output "기존 설치본을 $Backup 으로 백업합니다"
  if (Test-Path -LiteralPath $Backup) { Remove-Item -LiteralPath $Backup -Recurse -Force }
  Move-Item -LiteralPath $Target -Destination $Backup
}
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -LiteralPath (Join-Path $ScriptDir '.claude-plugin') -Destination $Target -Recurse
Copy-Item -LiteralPath (Join-Path $ScriptDir 'aml') -Destination $Target -Recurse

# 4. 다음 단계
#    Claude Code 에 그대로 붙여 넣을 수 있게 C:/Users/... 모양(슬래시)으로 보여 준다.
$ShowTarget = (Resolve-Path -LiteralPath $Target).ProviderPath -replace '\\', '/'
Write-Output @"
✓ 복사 완료: $ShowTarget

다음 — Claude Code 안에서 실행하세요:

  1. 마켓플레이스 추가:
     /plugin marketplace add $ShowTarget

  2. 플러그인 설치:
     /plugin install aml@automix-light

  3. 확인:
     /help                  # /aml:new, /aml:go, /aml:review, /aml:next 가 보이면 됩니다

"@
