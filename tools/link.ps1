# 把本仓库里每个真正的技能目录（含 SKILL.md）以 junction 形式链接到指定工具的 skills 目录。
# 用法: .\tools\link.ps1 <目标skills目录>
#   例如: .\tools\link.ps1 $env:USERPROFILE\.workbuddy\skills
#         .\tools\link.ps1 $env:USERPROFILE\.claude\skills
param(
  [Parameter(Mandatory=$true)][string]$Target
)
$src = Resolve-Path (Join-Path $PSScriptRoot "..")
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Get-ChildItem -Directory $src | ForEach-Object {
  if (Test-Path (Join-Path $_.FullName "SKILL.md")) {
    $link = Join-Path $Target $_.Name
    if (Test-Path $link) { Write-Host "skip (已存在) $($_.Name)"; return }
    # Junction 不需要管理员权限，跨会话可用
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
    Write-Host "linked $($_.Name) -> $link"
  }
}
Write-Host "完成。目标: $Target （建议将该目录视为只读引用，勿在内写中间文件）"
