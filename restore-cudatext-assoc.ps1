$ErrorActionPreference = 'Stop'
# 回滚：恢复备份中记录的文本文件关联（UserChoice 部分需在 GUI 重新选择）
$cand = Join-Path $PSScriptRoot 'assoc-backup\original-backup.json'; $latest = if (Test-Path -LiteralPath $cand) { $cand } else { Join-Path $PSScriptRoot 'assoc-backup\latest.json' }
if (-not (Test-Path -LiteralPath $latest)) { throw '未找到备份 assoc-backup\latest.json，无法回滚' }
$b = Get-Content -LiteralPath $latest -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($en in $b.entries) {
  $hkPath = "HKCU:\Software\Classes\" + $en.ext
  if ($en.oldDefault -ne '') { New-Item -Force -Path $hkPath | Out-Null; Set-ItemProperty -LiteralPath $hkPath -Name '(default)' -Value $en.oldDefault; Write-Output ("{0}: 已还原 HKCU 默认关联 [{1}]" -f $en.ext, $en.oldDefault) }
  else { New-Item -Force -Path $hkPath | Out-Null; Set-ItemProperty -LiteralPath $hkPath -Name '(default)' -Value ''; Write-Output ("{0}: 已清空 HKCU 默认关联" -f $en.ext) }
  if ($en.oldUserChoice -ne '') { Write-Output ("{0}: 原 UserChoice=[{1}] 无法自动还原（Windows 校验哈希），请在右键→打开方式 中重新勾选“始终使用”" -f $en.ext, $en.oldUserChoice) }
}
Write-Output '回滚完成（部分需 GUI 手动还原，见上方提示）。'