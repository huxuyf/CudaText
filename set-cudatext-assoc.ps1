$ErrorActionPreference = 'Stop'
# 设置常见文本文件默认打开程序为 CudaText（用户级，无需管理员权限）
# 每个扩展名使用独立 ProgID，并配置各自的文件类型图标（图标来自 data\assoc_icons）
$exe = Join-Path $PSScriptRoot 'cudatext.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw "未找到 CudaText: $exe" }
$exe = (Get-Item -LiteralPath $exe).FullName
$iconDir = Join-Path $PSScriptRoot 'data\assoc_icons'
if (-not (Test-Path -LiteralPath $iconDir)) { throw "未找到图标目录: $iconDir" }

$exts = [ordered]@{
  '.txt'        = @{ icon = 'hd\text.ico';         desc = '文本文档' }
  '.md'         = @{ icon = 'hd\markdown.ico';     desc = 'Markdown 文档' }
  '.log'        = @{ icon = 'hd\log.ico';          desc = '日志文件' }
  '.json'       = @{ icon = 'hd\json.ico';         desc = 'JSON 文档' }
  '.xml'        = @{ icon = 'hd\xml.ico';          desc = 'XML 文档' }
  '.ini'        = @{ icon = 'hd\ini.ico';          desc = 'INI 配置文件' }
  '.cfg'        = @{ icon = 'hd\config_cfg.ico';   desc = '配置文件' }
  '.csv'        = @{ icon = 'hd\csv.ico';          desc = 'CSV 表格' }
  '.yaml'       = @{ icon = 'hd\yaml.ico';         desc = 'YAML 文档' }
  '.yml'        = @{ icon = 'hd\yaml.ico';         desc = 'YAML 文档' }
  '.html'       = @{ icon = 'hd\html.ico';         desc = 'HTML 文档' }
  '.css'        = @{ icon = 'hd\css.ico';          desc = 'CSS 样式表' }
  '.js'         = @{ icon = 'hd\js.ico';           desc = 'JavaScript 文件' }
  '.py'         = @{ icon = 'hd\python.ico';       desc = 'Python 脚本' }
  '.conf'       = @{ icon = 'hd\config_conf.ico';  desc = '配置文件' }
  '.toml'       = @{ icon = 'hd\toml.ico';         desc = 'TOML 文档' }
  '.sql'        = @{ icon = 'hd\sql.ico';          desc = 'SQL 脚本' }
  '.properties' = @{ icon = 'hd\config_props.ico'; desc = '属性文件' }
  '.c'          = @{ icon = 'hd\c.ico';          desc = 'C 源文件' }
  '.h'          = @{ icon = 'hd\c.ico';          desc = 'C 头文件' }
  '.cpp'        = @{ icon = 'hd\cpp.ico';        desc = 'C++ 源文件' }
  '.cc'         = @{ icon = 'hd\cpp.ico';        desc = 'C++ 源文件' }
  '.cxx'        = @{ icon = 'hd\cpp.ico';        desc = 'C++ 源文件' }
  '.hpp'        = @{ icon = 'hd\cpp.ico';        desc = 'C++ 头文件' }
  '.hxx'        = @{ icon = 'hd\cpp.ico';        desc = 'C++ 头文件' }
  '.hh'         = @{ icon = 'hd\cpp.ico';        desc = 'C++ 头文件' }
  '.ipp'        = @{ icon = 'hd\cpp.ico';        desc = 'C++ 内联实现' }
  '.cs'         = @{ icon = 'hd\csharp.ico';     desc = 'C# 源文件' }
  '.csx'        = @{ icon = 'hd\csharp.ico';     desc = 'C# 脚本' }
  '.java'       = @{ icon = 'hd\java.ico';       desc = 'Java 源文件' }
  '.go'         = @{ icon = 'hd\go.ico';         desc = 'Go 源文件' }
  '.rs'         = @{ icon = 'hd\rust.ico';       desc = 'Rust 源文件' }
  '.kt'         = @{ icon = 'hd\kotlin.ico';     desc = 'Kotlin 源文件' }
  '.kts'        = @{ icon = 'hd\kotlin.ico';     desc = 'Kotlin 脚本' }
  '.mjs'        = @{ icon = 'hd\js.ico';         desc = 'JavaScript 模块' }
  '.ts'         = @{ icon = 'hd\typescript.ico'; desc = 'TypeScript 源文件' }
  '.tsx'        = @{ icon = 'hd\typescript.ico'; desc = 'TypeScript JSX' }
  '.py3'        = @{ icon = 'hd\python.ico';     desc = 'Python 3 脚本' }
  '.pyw'        = @{ icon = 'hd\python.ico';     desc = 'Python 窗口脚本' }
  '.pyi'        = @{ icon = 'hd\python.ico';     desc = 'Python 存根' }
  '.sh'         = @{ icon = 'hd\shell.ico';      desc = 'Shell 脚本' }
  '.bash'       = @{ icon = 'hd\shell.ico';      desc = 'Bash 脚本' }
  '.zsh'        = @{ icon = 'hd\shell.ico';      desc = 'Zsh 脚本' }
  '.ksh'        = @{ icon = 'hd\shell.ico';      desc = 'KornShell 脚本' }
  '.csh'        = @{ icon = 'hd\shell.ico';      desc = 'C Shell 脚本' }
  '.fish'       = @{ icon = 'hd\shell.ico';      desc = 'Fish 脚本' }
  '.bat'        = @{ icon = 'hd\batch.ico';      desc = '批处理文件' }
  '.cmd'        = @{ icon = 'hd\batch.ico';      desc = '命令脚本' }
  '.ps1'        = @{ icon = 'hd\powershell.ico'; desc = 'PowerShell 脚本' }
  '.psm1'       = @{ icon = 'hd\powershell.ico'; desc = 'PowerShell 模块' }
  '.psd1'       = @{ icon = 'hd\powershell.ico'; desc = 'PowerShell 数据文件' }
  '.asm'        = @{ icon = 'hd\assembly.ico';   desc = '汇编源文件' }
  '.diff'       = @{ icon = 'hd\diff.ico';       desc = 'Diff 文件' }
  '.patch'      = @{ icon = 'hd\diff.ico';       desc = '补丁文件' }
  '.rst'        = @{ icon = 'hd\rst.ico';        desc = 'reStructuredText 文档' }
  '.markdown'   = @{ icon = 'hd\markdown.ico';   desc = 'Markdown 文档' }
  '.mkd'        = @{ icon = 'hd\markdown.ico';   desc = 'Markdown 文档' }
  '.jsonl'      = @{ icon = 'hd\json.ico';       desc = 'JSON Lines 文档' }
  '.xsd'        = @{ icon = 'hd\xml.ico';        desc = 'XML Schema' }
  '.xsl'        = @{ icon = 'hd\xml.ico';        desc = 'XSL 样式表' }
  '.xslt'       = @{ icon = 'hd\xml.ico';        desc = 'XSL 转换' }
}

$missing = @()
foreach ($e in $exts.Keys) {
  $p = Join-Path $iconDir $exts[$e].icon
  if (-not (Test-Path -LiteralPath $p)) { $missing += $p }
}
if ($missing.Count) { throw ("缺少图标文件: " + ($missing -join '; ')) }

# 1) 备份当前关联
$backupDir = Join-Path $PSScriptRoot 'assoc-backup'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$capKey = 'HKCU:\Software\Classes\CudaText.Capabilities\FileAssociations'
$entries = @()
foreach ($e in $exts.Keys) {
  $hk = Get-ItemProperty -LiteralPath ("HKCU:\Software\Classes\" + $e) -ErrorAction SilentlyContinue
  $oldDef = if ($null -ne $hk) { [string]$hk.'(default)' } else { '' }
  $oldIcon = [string](Get-ItemProperty -LiteralPath ("HKCU:\Software\Classes\" + $e + '\DefaultIcon') -ErrorAction SilentlyContinue).'(default)'
  $uckPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\" + $e + '\UserChoice'
  $uck = Get-ItemProperty -LiteralPath $uckPath -ErrorAction SilentlyContinue
  $oldUc = if ($null -ne $uck) { [string]$uck.ProgId } else { '' }
  $cap = [string](Get-ItemProperty -LiteralPath $capKey -Name $e -ErrorAction SilentlyContinue).$e
  $entries += [pscustomobject]@{ ext = $e; oldDefault = $oldDef; oldExtIcon = $oldIcon; oldUserChoice = $oldUc; oldCapability = $cap }
}
$backup = [pscustomobject]@{ timestamp = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); exe = $exe; entries = $entries }
$latest = Join-Path $backupDir 'latest.json'
[IO.File]::WriteAllText($latest, ($backup | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding $true))

# 2) 保留共享 ProgID 作为兜底
$cmdPath = "HKCU:\Software\Classes\CudaText\shell\open\command"
$icPath  = "HKCU:\Software\Classes\CudaText\DefaultIcon"
New-Item -Force -Path $cmdPath | Out-Null
New-Item -Force -Path $icPath | Out-Null
Set-ItemProperty -LiteralPath $cmdPath -Name '(default)' -Value ('"' + $exe + '" "%1"')
Set-ItemProperty -LiteralPath $icPath  -Name '(default)' -Value ($exe + ',0')

# 3) 每个扩展名独立 ProgID + 扩展名级图标
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class CudaReg {
  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  private static extern int RegDeleteKeyEx(IntPtr hKey, string lpSubKey, uint samDesired, uint lpReserved);
  public static void DeleteKey(string subKey) {
    RegDeleteKeyEx(unchecked((IntPtr)0x80000001), subKey, 0, 0);
  }
}
"@
foreach ($e in $exts.Keys) {
  $progId = 'CudaText' + $e
  $icon = Join-Path $iconDir $exts[$e].icon
  $extKey = "HKCU:\Software\Classes\" + $e
  $progKey = "HKCU:\Software\Classes\" + $progId

  New-Item -Force -Path "$progKey\shell\open\command" | Out-Null
  New-Item -Force -Path "$progKey\DefaultIcon" | Out-Null
  Set-ItemProperty -LiteralPath $progKey -Name '(default)' -Value $exts[$e].desc
  Set-ItemProperty -LiteralPath "$progKey\shell\open\command" -Name '(default)' -Value ('"' + $exe + '" "%1"')
  Set-ItemProperty -LiteralPath "$progKey\DefaultIcon" -Name '(default)' -Value ('"' + $icon + '"')

  New-Item -Force -Path $extKey | Out-Null
  Set-ItemProperty -LiteralPath $extKey -Name '(default)' -Value $progId
  # 部分系统扩展名会忽略 ProgID 的 DefaultIcon，扩展名级图标作为兜底
  New-Item -Force -Path "$extKey\DefaultIcon" | Out-Null
  Set-ItemProperty -LiteralPath "$extKey\DefaultIcon" -Name '(default)' -Value ('"' + $icon + '"')

  New-Item -Force -Path $capKey | Out-Null
  Set-ItemProperty -LiteralPath $capKey -Name $e -Value $progId

  # 解除 UserChoice / UserChoiceLatest 锁定，使扩展名默认程序生效
  $feBase = "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\" + $e
  [CudaReg]::DeleteKey($feBase + '\UserChoice')
  [CudaReg]::DeleteKey($feBase + '\UserChoiceLatest')
  Write-Output ("{0}: 已关联 {1} 并设置图标（已解除原 UserChoice 锁定）" -f $e, $exts[$e].icon)
}
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class CudaAssocRefresh {
  [DllImport("shell32.dll")] public static extern void SHChangeNotify(int ev, uint flags, IntPtr a, IntPtr b);
}
"@
[CudaAssocRefresh]::SHChangeNotify(0x08000000, 0x1000, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Output ""
Write-Output ("完成。备份文件: {0}" -f $latest)
