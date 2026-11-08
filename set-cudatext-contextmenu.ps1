# 将 CudaText 添加到资源管理器右键菜单（文件/文件夹/空白处/磁盘）与"发送到"菜单
# 集成方式参考本机 EmEditor：用户级 HKCU\Software\Classes 注册 + %APPDATA%\Microsoft\Windows\SendTo 快捷方式，无需管理员权限
# 用法：直接运行 = 安装；加参数 -Uninstall = 卸载（或运行 CudaText-右键菜单-安装.bat uninstall）

param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$exe = Join-Path $PSScriptRoot 'cudatext.exe'
if (-not (Test-Path -LiteralPath $exe)) {
  $exe = Join-Path $PSScriptRoot 'cudatext64.exe'
}
if (-not (Test-Path -LiteralPath $exe)) { throw "未找到 CudaText 可执行文件: $PSScriptRoot" }
$exe   = (Get-Item -LiteralPath $exe).FullName
$verb  = 'CudaText'
$label = '用 CudaText 打开'

$sendToDir = [Environment]::GetFolderPath('SendTo')
$lnkPath   = Join-Path $sendToDir ($verb + '.lnk')

function Add-ShellVerb {
  param([string]$Key, [string]$Arg, [string]$Desc)
  $base = "HKCU:\Software\Classes\$Key\shell\$verb"
  New-Item -Force -Path "$base\command" | Out-Null
  Set-ItemProperty -LiteralPath $base         -Name '(default)' -Value $label
  Set-ItemProperty -LiteralPath $base         -Name 'Icon'      -Value ($exe + ',0')
  Set-ItemProperty -LiteralPath "$base\command" -Name '(default)' -Value ('"' + $exe + '" "' + $Arg + '"')
  Write-Output ("右键菜单[{0}]: 已添加 [{1}]" -f $Desc, $label)
}

function Remove-ShellVerb {
  param([string]$Key, [string]$Desc)
  $base = "HKCU:\Software\Classes\$Key\shell\$verb"
  if (Test-Path -LiteralPath $base) { Remove-Item -LiteralPath $base -Recurse -Force; Write-Output ("右键菜单[{0}]: 已移除" -f $Desc) }
}

if ($Uninstall) {
  Remove-ShellVerb '*'                    '文件'
  Remove-ShellVerb 'Directory'            '文件夹'
  Remove-ShellVerb 'Directory\Background' '文件夹空白处'
  Remove-ShellVerb 'Drive'                '磁盘'
  if (Test-Path -LiteralPath $lnkPath) { Remove-Item -LiteralPath $lnkPath -Force; Write-Output '发送到: 已移除 CudaText.lnk' }
  Write-Output '卸载完成。'
} else {
  Add-ShellVerb '*'                    '%1' '文件'
  # Add-ShellVerb 'Directory'            '%1' '文件夹'
  # Add-ShellVerb 'Directory\Background' '%V' '文件夹空白处'
  # Add-ShellVerb 'Drive'                '%V' '磁盘'

  $wsh = New-Object -ComObject WScript.Shell
  $lnk = $wsh.CreateShortcut($lnkPath)
  $lnk.TargetPath      = $exe
  $lnk.WorkingDirectory = Split-Path -Parent $exe
  $lnk.IconLocation    = $exe + ',0'
  $lnk.Save()
  Write-Output ("发送到: 已创建 {0}" -f $lnkPath)
  Write-Output '完成。右键文件/文件夹/空白处即可看到"用 CudaText 打开"，资源管理器无需重启。'
}
