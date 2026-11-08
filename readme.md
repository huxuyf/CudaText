# CudaText（中文本地化分支）

基于 [CudaText](https://cudatext.github.io) 1.239.0.1 的跨平台文本编辑器分支，使用 Free Pascal + Lazarus 编写，遵循 Mozilla Public License 2.0。

本仓库在保留上游全部功能的基础上，重点做了三件事：**界面中文化**、**内置插件与图标整合**、**代码树与文件操作的稳定性改进**。

## 与上游版本的差异

| 方向 | 本仓库改动 |
|---|---|
| 界面语言 | 主程序界面文案以中文编写；内置插件菜单、对话框提供 `zh_CN` 语言包（`app/data/langmenu`、`app/data/langpy`） |
| 应用图标 | Windows `.ico`、Linux 512px PNG、macOS `.icns` 统一为新版蓝色图标；文件类型图标针对亮/暗背景重新设计 |
| 界面图标 | 侧栏与工具栏图标按 [ICON-SPEC.md](doc/ICON-SPEC.md) 的几何规范重制 |
| 内置插件 | 仓库直接内置 32 个常用 Python 插件（命令面板、项目管理、代码片段、LSP、格式化、终端、差异对比等），无需首次启动后再下载 |
| 词法器 | 内置 28 种语言的词法器定义（`app/data/lexlib`），其余可通过 Addon Manager 安装 |
| 主题可读性 | 新增 WCAG 对比度审计工具（[tools/theme_wcag](tools/theme_wcag)），并生成 `syn_wcag`、`sub_wcag` 派生主题 |
| 代码树性能 | 仅对当前活动编辑器重建代码树；连续输入按 2000 ms 去抖；无变化事件按版本签名跳过；后台标签的缓存树在切回时延迟重填 |
| 稳定性 | 修正 Python 桥引用计数与插件导入失败处理；`ProcessMessages` 后增加对象存活检查；收紧编辑器 API 句柄校验；文件与会话改为临时文件 + 原子替换保存 |
| 构建 | 版本号统一由 `setup/cuda_ver.sh` 维护；macOS 由 GitHub Actions 从本仓库源码构建 Intel 与 Apple Silicon 两种 DMG |

## 主要功能

CudaText 本身是一款轻量但功能完整的编辑器：

- 多标签页、标签分组、标签恢复与标签列表
- 多光标、列选择、矩形选择、括号配对、代码折叠
- 代码树（CodeTree）与 Markdown / reStructuredText 等结构化大纲
- 自动完成（含 HTML/CSS/JS 等片段）、代码片段面板、Emmet
- 28 种内置语法高亮，可按需扩展词法器
- 项目管理器、会话保存、上次打开位置恢复
- 查找/替换（当前文件与多文件）、增量查找、正则表达式
- 外部工具、终端面板、差异对比、格式化插件、LSP 客户端
- 支持 Windows、Linux（GTK2/GTK3/Qt5/Qt6）、macOS（Cocoa），并提供 BSD / Solaris / Haiku 构建脚本
- 便携模式：可执行文件与 `data`、`py` 相邻即可，不写系统注册表

## 快速开始

### Windows

仓库中的 `app/bin/windows-amd64` 已包含可直接运行的 Windows x64 版本及其 Python 运行库：

```
app\bin\windows-amd64\cudatext.exe
```

直接双击运行即可。首次启动会在同目录生成 `settings` 个人配置目录；分发时不要包含该目录。

### 便携模式

将 `cudatext.exe` 与 `data`、`py`、`settings_default` 放在同一目录即为便携模式。`settings` 目录保存当前用户配置与历史记录。

## 从源码构建

### 依赖

编译前需在 Lazarus 中安装以下包（源码由各自仓库提供）：

* https://github.com/bgrabitmap/bgrabitmap
* https://github.com/Alexey-T/EncConv
* https://github.com/Alexey-T/ATBinHex-Lazarus
* https://github.com/Alexey-T/ATFlatControls
* https://github.com/Alexey-T/ATSynEdit
* https://github.com/Alexey-T/ATSynEdit_Cmp
* https://github.com/Alexey-T/EControl
* https://github.com/Alexey-T/ATSynEdit_Ex
* https://github.com/Alexey-T/Python-for-Lazarus
* https://github.com/Alexey-T/Emmet-Pascal

### Windows x64

```bat
lazbuild --bm="windows x64" app\cudatext.lpi
```

产物输出到 `app\bin\windows-amd64\cudatext.exe`。对应的 Lazarus 构建模式还提供 `windows x32`、`windows aarch64`。

### Linux

选择与目标桌面环境一致的构建模式：

```sh
lazbuild --bm="linux x64 gtk3" app/cudatext.lpi
```

可用模式：`linux x64 gtk2`、`linux x64 gtk3`、`linux x64 qt5`、`linux x64 qt6`，以及 ARM / AArch64 的 GTK2、Qt5 变体。需先安装对应 widgetset 的开发库。

### macOS

本地构建使用 `macos x64` 或 `macos aarch64` 模式（Cocoa widgetset）。仓库也提供 GitHub Actions 工作流 [build-macos.yml](.github/workflows/build-macos.yml)，可手动触发（`workflow_dispatch`）构建两种架构的 DMG，产物以 workflow artifact 形式上传，不创建 Release 或 tag。

### 版本号维护

`setup/cuda_ver.sh` 是版本号的唯一来源。修改后运行：

```sh
sh setup/sync_version.sh          # 写入 proc_msg.pas、cudatext.lpi、Info.plist、changelog、deb control
sh setup/sync_version.sh --check  # 仅校验，供 CI 使用
```

## 目录结构

| 路径 | 说明 |
|---|---|
| `app/` | Pascal 主程序源码、Lazarus 工程（`cudatext.lpi`）与运行时资源 |
| `app/bin/windows-amd64/` | Windows x64 可执行文件、Qt/Python 运行库与便携资源 |
| `app/data/` | 词法器、主题、图标、片段、语言包等运行数据 |
| `app/py/` | 内置 Python 插件与 CudaText Python API |
| `app/settings_default/` | 默认配置（`default.json` 等） |
| `doc/` | 界面 Token 与图标规范 |
| `setup/` | Windows / Linux / macOS / BSD 构建与打包脚本 |
| `tools/` | 主题对比度审计、插件下载等辅助工具 |
| `testfiles/`、`testapps/` | 测试文件与测试工程 |
| `wiki/` | 插件、API、格式等说明文档 |

## 文档

- 界面颜色 Token 说明：[doc/DESIGN-TOKENS.md](doc/DESIGN-TOKENS.md)
- 图标几何与配色规范：[doc/ICON-SPEC.md](doc/ICON-SPEC.md)
- 版本历史：[app/readme/history.txt](app/readme/history.txt)
- 上游完整文档：https://wiki.freepascal.org/CudaText
- 插件 API 文档：https://wiki.freepascal.org/CudaText_API
- 编译说明（上游 Wiki）：https://wiki.freepascal.org/CudaText#How_to_compile_CudaText

## 许可证

本项目遵循 Mozilla Public License 2.0，详见 [LICENSE](LICENSE)。源码与图标基于上游 CudaText 及其依赖组件，相关第三方许可证见 `app/readme/` 下的 `license.*` 文件。
