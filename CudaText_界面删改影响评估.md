# CudaText 界面删改影响评估

> 本文仅为影响评估，**未执行任何删除或代码修改**。
> 评估范围：界面显示层（菜单 / 工具栏 / 面板 / 布局）与后台代码层（Pascal 内核、配置读写、Python API、主题、构建脚本、随附插件）。
> 仓库：`c:\Users\user\Desktop\CudaText`（当前 Windows 运行目录 `app\bin\windows-amd64`）。

---

## 0. 结论摘要

### 0.1 风险分级

| # | 删除项 | 风险等级 | 一句话结论 |
|---|--------|----------|------------|
| 1 | Minimap | 中 | CudaText 侧只有 UI / 配置 / API；渲染器在外部 ATSynEdit 组件，**本仓库无法真正删除渲染逻辑**，只能关闭与清理入口 |
| 2 | Micromap | 中 | 绘制逻辑在本仓库（`proc_editor_micromap.pas`），可真正删除；但牵连滚动条回调、主题色、每文件历史状态、Python 属性 |
| 3 | Sidebar | 高 | `PanelSide` 同时是**侧栏与底栏按钮条的宿主**，删除会直接改变 4/5/6/7 的可用性 |
| 4 | Side panel | 极高 | 承载 Code-Tree 与 3 个内置插件（Project / Tabs / Snippet），并暴露核心 `app_proc` API |
| 5 | Bottom panel | 极高 | 承载 Console / Output / Validate、Python `app_log`、Python 运行输出与交互 |
| 6 | Floating side panel | 中高 | 逻辑集中在 `TAppPanelHost`；还需迁移已持久化的 `float_side` 状态 |
| 7 | Floating bottom panel | 中高 | 同上，另涉及 `float_bottom` 与 `/pos/bottom` |
| 8 | Help 下 Forum/Wiki/Report an issue/Check for updates | 低 | 纯入口与 URL 调用；需保留父菜单以维持插件 API |
| 9 | Split 菜单及其全部子项 | 中 | 菜单本身易删；但命令、帮助菜单位置判断、Python `top-groups`、分隔符需同步清理 |

### 0.2 三个必须先知道的架构事实

1. **Minimap 不是本仓库实现的**：`proc_editor.pas` 只做“把配置项赋给编辑器属性”（`app/proc_editor.pas:325-336`），绘制在外部 ATSynEdit 组件中；`app/lib` 内也没有 ATSynEdit 的 `.ppu`，说明它来自仓库外的 Lazarus 包。**真正删除 Minimap 渲染必须改外部组件或 fork，本仓库最多做到“关闭 + 清理所有入口”。**
2. **Sidebar 是面板按钮的宿主**：`AppPanels[TAppPanelId.Side].Toolbar := ToolbarSideTop`、`AppPanels[TAppPanelId.Btm].Toolbar := ToolbarSideLow`（`app/formmain.pas:3131,3146`），而这两个 toolbar 的物理位置就在 `PanelSide` 内（`app/formmain.lfm:36-83`）。所以删 Sidebar 会让侧栏/底栏**失去标签切换按钮条**。
3. **界面入口在三个层面同时存在**：主菜单（lfm）→ 命令系统（`proc_cmd.pas` 的 `M.Add` → 命令面板/热键对话框）→ Python API（`menu_proc` / `app_proc` / 编辑器属性）。只删菜单不删命令，会留下命令面板与热键配置入口；只删命令不删 API，会让内置/第三方插件报错。

---

## 1. 通用删改机制（9 项共享）

删任何一项之前，需要按下面 5 条链路逐一核对，否则容易出现“界面没了但功能仍可被调用”或“编译不过”。

### 1.1 菜单链路

- 控件定义：`app/formmain.lfm`（主菜单 118-666 行）＋ Pascal 发布字段：`app/formmain.pas:272-445`。
- 点击事件不是写在 lfm 里，而是在 `UpdateMenuItemHotkey()` 中统一赋值：`app/formmain_updates_proc.inc:869-900`。
- 勾选/可用状态：`app/formmain_updates_proc.inc:1207-1300`（`UpdateMenuChecks_Frame/Global`）。
- 菜单被用户自定义时有“影子菜单项”`*_Alt` 记录：`app/formmain.pas:677-705`、`app/formmain_updates_proc.inc:963-1014`。
- 顶部菜单顺序被硬编码用于判断“是否标准菜单”：`app/formmain.pas:4320-4338`（其中 `MainMenu.Items[Count-2]=mnuSplit`）。

### 1.2 命令链路

- 命令码与名称：`app/proc_cmd.pas`（`M.Add(...)` 注册进 `AppKeymapMain`）。
- 命令面板 / 热键对话框：`app/form_menu_commands.pas:226`、`app/form_keys.pas:66` 直接枚举 `AppKeymapMain`。
- 命令分发：`app/formmain_cmd.inc`（`DoCommand` 的 `case`）。
- 命令分类列表：`app/proc_cmd.pas:824-970`（`IsCommandNeedTimer`）、`972`（`IsCommandHandledFromFindDialog`）、`1017`（`IsCommandForMacros`）。

### 1.3 Python API 链路

- Python 常量：`app/proc_py_const.pas`、`app/py/cudatext.py`、`app/py/cudax_lib.py`。
- 实现：`app/formmain_py_api.inc`。
- 菜单 ID 映射：`app/formmain_py_api.inc:428-479`（`PyHelper_MenuItemFromId`）。
- 注意：第三方插件通过数字常量调用；**删除常量比保留常量但返回失败更容易让插件直接抛异常**。

### 1.4 配置链路

- 默认值：`app/settings_default/default.json`（同时存在 macOS 副本 `app/cudatext.app/Contents/Resources/settings_default/default.json`）。
- 字段：`app/proc_globdata.pas`（`TUiOps` / `TEditorOps`）。
- 读写：`app/formmain_loadsave.inc`。
- 用户状态：运行时 `app/bin/windows-amd64/settings/user.json`、`history.json`。**当前 `history.json` 已存在 `"float_side": true`（第 12 行）**，删除浮动能力时必须做状态迁移。

### 1.5 资源 / 翻译 / 构建链路

- 语言模板：`app/data/lang/translation template.ini`（菜单键见 116-121、139-148、188-193 行）。
- 本地化调用：`app/formmain_translation.inc`。
- 主题色：`app/proc_colors.pas` + `app/data/themes/*.cuda-theme-ui`（macOS 副本同目录）。
- 构建：`app/cudatext.lpi` / `app/cudatext.lpr`（新增/删除 Pascal 单元时两者都要同步）。
- 运行副本：改动需同步到 `app/bin/windows-amd64/{py,data,settings_default}`（macOS 为 `app/cudatext.app/Contents/Resources/...`）。

---

## 2. 逐项影响评估

### 2.1 删除 Minimap

**界面位置**
- 主菜单 `View → Minimap`：`app/formmain.lfm:452-454`。
- 主工具栏按钮 “Toggle minimap”（图标 `map`）：`app/formmain_updates_proc.inc:1561`。
- 命令面板 / 热键对话框中的 `ui: toggle minimap` 命令（`cCommand_ToggleMinimap`）。

**受影响的关联功能与依赖**
- 每文件历史状态：`form_frame.pas:4193-4194`（保存 `cHistory_Minimap`）、`4460`（按历史恢复）。
- 文档级“已修改属性”`TATEditorModifiedOption.MinimapVisible`（`proc_editor.pas:325-326,2066-2067`）。
- Minimap tooltip、宽度、左侧、缩放、拖拽等 10 个配置项。
- 主题颜色：`EdMinimapBorder` / `EdMinimapTooltipBg` / `EdMinimapTooltipBorder`（`proc_colors.pas:42-44,514-516`；8 个内置主题文件第 18-20 行）。
- Python 编辑器属性：`PROP_MINIMAP`(44)、`PROP_MINIMAP_CHAR_WIDTH`(160)、`PROP_MINIMAP_AT_LEFT`(161)、`PROP_MINIMAP_SCALE`(162)。
- Python 颜色 ID：`COLOR_ID_MinimapBorder` / `MinimapTooltipBg` / `MinimapTooltipBorder`（`app/py/cudatext.py:673-675`）。
- 预览编辑器会主动关闭 Minimap：`form_unprinted.pas:105`、`proc_customdialog.pas:750`。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.pas` | 398, 677 | 菜单字段 / `_Alt` 记录 |
| `app/formmain_updates_proc.inc` | 982, 1131, 1241, 1252-1253, 1561 | `_Alt` 记录、热键、勾选、启用、工具栏按钮 |
| `app/formmain_loadsave.inc` | 1611-1621 | 读取 `minimap_*` |
| `app/proc_globdata.pas` | 647-657, 1964-1974 | `TEditorOps` 字段与默认值 |
| `app/proc_editor.pas` | 325-336, 788-790, 848-850, 902-904 | 应用到编辑器 / 主题色 |
| `app/form_frame.pas` | 210, 594, 4193-4194, 4460 | 每文件历史 |
| `app/proc_colors.pas` | 42-44, 514-516 | 主题色枚举与默认值 |
| `app/data/themes/*.cuda-theme-ui` | 18-20 | `EdMinimap*` 键（8 个主题） |
| `app/formmain_py_api.inc` | 4018-4028, 4909-4929 | Python 属性读写 |
| `app/proc_py_const.pas` / `cudatext.py` | 204/305-306；209/311-313 | Python 常量 |
| `app/settings_default/default.json` | 563-607 | 配置项与注释（设置面板自动生成条目） |

**风险点**
- **无法在本仓库真正删除渲染器**：只能强制 `OptMinimapVisible=false` 并删除入口；外部 ATSynEdit 升级时 Minimap 代码仍会一起编译。
- 若删除 `PROP_MINIMAP*` 常量，使用该属性的第三方插件会抛 `AttributeError`；若保留常量但强制关闭，则是“静默无效”，兼容性更好。
- 删除 `minimap_*` 配置项后，用户旧 `user.json` 中同名字段会被忽略（不报错），但设置面板中条目消失，需要在文档中说明。
- 每文件历史中的 `/minimap` 键会变成孤儿数据，无功能影响。

**删除后如何验证**
1. 构建：`lazbuild app/cudatext.lpi --bm="windows x64"`（若改了 include 文件，先删 `app/lib` 下 `.ppu` 或加 `-B` 全量构建）。
2. 启动 `app\bin\windows-amd64\cudatext.exe`。
3. 界面：`View` 菜单无 Minimap；工具栏无 `map` 按钮；命令面板（`Command palette...`）与“热键”对话框中无 toggle minimap 项。
4. 配置：在 `settings/user.json` 写 `"minimap_show": true` 与在 `history.json` 某文件节点写 `"/minimap":1`，重启后编辑器仍无 Minimap、无异常日志。
5. 预览场景：打开“Unprinted chars...”与任一插件自定义对话框，编辑器正常显示。
6. 若保留 Python 常量：插件调用 `ed.get_prop(PROP_MINIMAP)` 应返回 False；若删除常量：确认内置 Python 代码（`cudax_lib.py:57-60`）已同步，无 `NameError`。

---

### 2.2 删除 Micromap

**界面位置**
- 主菜单 `View → Micromap`：`app/formmain.lfm:455-457`。
- 命令面板 / 热键：`ui: toggle micromap`（`cCommand_ToggleMicromap`）。
- 本项**没有**主工具栏按钮。

**受影响的关联功能与依赖**
- 完全在本仓库实现的绘制单元：`app/proc_editor_micromap.pas`（负责行状态、选中、书签、插件标记、当前视区）。
- 绘制钩子：`form_frame.pas:2357`（`OnClickMicromap`）、`2377`（`OnDrawMicromap`）、`3954-3957`。
- “Micromap 画在垂直滚动条上”的特殊路径：`form_frame.pas:3959-3973`（`EditorDrawScrollbarVert` 会接管滚动条绘制）。
- 位图缓存 `FMicromapBmp`：`form_frame.pas:210, 4001-4008, 2523-2524`。
- 每文件历史 `/micromap`：`form_frame.pas:4196-4197, 4449-4453`。
- 插件标记的 micromap 模式：`TATMarkerMicromapMode.TextOnly`（`formmain_find.inc:55`、`proc_editor.pas:2340`）。
- 主题色 4 个：`EdMicromapBg/ViewBg/Occur/Spell`（`proc_colors.pas:45-48,517-520`，8 个主题文件 21-24 行）。
- Python 属性：`PROP_MICROMAP`(45)、`PROP_MICROMAP_WIDTH`(53)、`PROP_MICROMAP_ON_SCROLLBAR`(56)、`PROP_MICROMAP_AT_LEFT`(57)。
- 预览编辑器：`form_find.lfm:220,266`（设计期设为 True）、`form_unprinted.pas:106`、`proc_customdialog.pas:752`。
- 性能保护：`UiOps.MaxLinesForMicromapPaint`（`proc_globdata.pas:271,2326`）、`MicromapMinMarkHeight/MicromapMinViewareaHeight`（553-554）。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.lfm` | 455-457 | 菜单项 |
| `app/formmain.pas` | 388, 678 | 字段 / `_Alt` |
| `app/formmain_updates_proc.inc` | 983, 1132, 1242, 1254-1255 | `_Alt`、热键、勾选、启用 |
| `app/proc_editor_micromap.pas` | 全文件（1-375） | 绘制实现 |
| `app/cudatext.lpr` / `app/cudatext.lpi` | 16 / 1666 | 单元引用，删除时两处都要改 |
| `app/form_frame.pas` | 210, 240, 315, 594, 2357, 2377, 2523-2524, 3954-3973, 4001-4008, 4196-4197, 4449-4453 | 钩子、缓存、历史 |
| `app/proc_editor.pas` | 338-343, 2040-2041, 2068-2069, 2856 | 属性应用/同步 |
| `app/proc_globdata.pas` | 659-663, 1976-1980, 271, 553-554 | 配置与常量 |
| `app/formmain_loadsave.inc` | 1623-1626 | 读取 `micromap_*` |
| `app/proc_colors.pas` | 45-48, 517-520 | 主题色 |
| `app/data/themes/*.cuda-theme-ui` | 21-24 | 主题键 |
| `app/formmain_py_api.inc` | 4030-4040, 4924-4937 | Python 属性 |
| `app/proc_py_const.pas` / `cudatext.py` | 205/213/216-217；210/218/221-222 | Python 常量 |

**风险点**
- 删除 `OnDrawMicromap` 钩子后，若仍保留 `EditorDrawScrollbarVert` 中 `OptMicromapOnScrollbar` 判断，必须在 `form_frame.pas:3959-3973` 恢复“滚动条自行绘制”，否则滚动条可能空白或不重绘。
- 删除 `proc_editor_micromap.pas` 必须同时改 `.lpr` 与 `.lpi`，否则构建失败；构建缓存需清理。
- 主题色枚举删除后，主题文件里的 `EdMicromap*` 键会变成未识别键（读取时会被忽略），但主题编辑器/文档需要同步。
- 每文件历史 `/micromap`、`micromap_*` 配置遗留数据无功能影响，但会增加“看起来仍支持”的误解，建议一并从 `default.json` 移除。
- 与 Minimap 不同，此功能**可以真正删除**，因此回归面更广（滚动条、书签、插件标记、spellchecker 标记刷新）。

**删除后如何验证**
1. 构建并启动。
2. `View` 菜单无 Micromap；命令面板/热键对话框无 micromap 项。
3. `micromap_show:true` + `micromap_on_scrollbar:true` 写入配置后重启：无 Micromap、垂直滚动条拖动/滚轮/翻页正常（重点验证滚动条回调没有残留）。
4. 打开大文件（超过 300k 行）与普通文件，滚动、书签跳转、查找全部标记、拼写检查标记均正常，无崩溃。
5. 打开 Find/Replace 对话框并让编辑器内容变化，原预览编辑器不出现窄条绘制。
6. 检查 `app/bin/windows-amd64/cudatext_error.log` 无异常。

---

### 2.3 删除 Sidebar（左侧/右侧竖条 `PanelSide`）

**界面位置**
- `PanelSide`：`app/formmain.lfm:29-84`，内部三个 toolbar：
  - `ToolbarSideTop`（标签为侧栏面板按钮 + 菜单按钮“3 点”）
  - `ToolbarSideMid`（Find 按钮）
  - `ToolbarSideLow`（底栏面板按钮 Console/Output/Validate）
- 主菜单 `View → Sidebar`：`app/formmain.lfm:474-476`。
- 侧栏图标来自 `app/data/sideicons/{common_20x20|octicons_20x20}`（`common_20x20` 当前含 12 个 png + `credits.txt`）。

**受影响的关联功能与依赖**
- **最关键的依赖**：它是 Side panel 和 Bottom panel 的 toolbar 宿主（见 0.2 第 2 条）。
- 菜单按钮“3 点”弹出主菜单副本：`formmain_sidepanel.inc:34-54`；显示策略由 `ui_menu_button` 控制：`formmain_updates_proc.inc:1966-1980`。
- 侧栏面板按钮（Code-Tree / Project / Tabs / Snippet / Console / Output / Validate）由 `TAppPanelHost.AddPanel` 动态加到 `ToolbarSideTop/Low`。
- 侧栏主题 / 图标尺寸 / 左右位置：`ui_sidebar_theme`、`ui_sidebar_on_right`；加载逻辑 `formmain_updates_proc.inc:1580-1629`。
- 面板状态角标（错误数/输出行数）：`formmain.pas:3798-3835`。
- 全屏/免打扰隐藏侧栏：`formmain.pas:7547,7560,7570`（`ui_fullscreen` 中的 `a`）。
- Python API：`PROC_SHOW_SIDEBAR_GET/SET`（`formmain_py_api.inc:6164-6169`）。
- 面板枚举 API 复用侧栏 toolbar：`PyHelper_EnumSidebar`（`formmain_py_api.inc:5517-5563`）。
- 插件图标加载复用侧栏 ImageList：`DoSidebar_FilenameToImageIndex`（`formmain_sidepanel.inc:57-65`），`ImageListSide` 定义在 `formmain.lfm:781`。
- 本地化：`formmain_translation.inc:346-355`。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.lfm` | 29-84, 781 | `PanelSide` + `ImageListSide` |
| `app/formmain.pas` | 468, 4897-4900, 5225-5226, 7061-7078, 7424-7428, 7547-7570 | 字段、显隐、左右、全屏 |
| `app/formmain_updates_proc.inc` | 1272, 1572-1578, 1580-1629, 1736-1739, 1966-1980 | 勾选、图标常量/加载、按钮初始化、菜单按钮策略 |
| `app/formmain_sidepanel.inc` | 34-65 | 菜单弹出、图标加载 |
| `app/formmain.pas` | 3798-3835 | 角标刷新 |
| `app/formmain_themes.inc` | 147-160, 199-201 | 侧栏与面板标题/分隔条主题 |
| `app/proc_globdata.pas` | 306-307, 485-486, 814, 1854, 2146-2147, 2371-2372 | `UiOps` 字段、图标目录、默认值 |
| `app/formmain_loadsave.inc` | 1832-1837 | 读取 `ui_sidebar_*`、`ui_menu_button` |
| `app/formmain_py_api.inc` | 6164-6169 | Python 显隐 API |
| `app/data/lang/translation template.ini` | 145, 188-193 等 | 文案键 |
| `app/settings_default/default.json` | 1700-1733 | `ui_sidebar_*`、`ui_menu_button` |

**风险点**
- **删除 Sidebar 而保留 4/5 项时，面板会失去按钮条**：`AppPanels[*].Toolbar` 指向被删除控件，必须改为“迁移 toolbar”或“移除面板级 toolbar 机制”，否则编译失败或运行时 AV。
- 侧栏被删后，菜单被隐藏（`ui_menu_show:false`）时用户将没有 “3 点” 入口，主菜单不可达（除非用热键/命令面板）。
- 插件图标加载依赖 `ImageListSide`；若删除，`DoSidebar_FilenameToImageIndex` 必须改为保留一个隐藏的 ImageList 或返回 0，否则内置插件面板图标异常。
- `ui_sidebar_show/_on_right/_theme/_menu_button`、`AppDir_DataSidebarIcons`、`sideicons` 图标资源都会变成死配置/死数据。
- `ui_fullscreen` 的 `a` 标志变成无效字符（无害，但文档需更新）。
- 布局：`PanelAll.Left=75` 是设计期值，删除 `PanelSide` 后运行时会按 `alClient` 重新铺满，但需实机确认没有 75px 空白。

**删除后如何验证**
1. 构建通过（特别注意 `formmain.lfm` 与 `formmain.pas` 字段一致性）。
2. 启动后窗口左侧（或右侧）无竖条，编辑区铺满；`View` 菜单无 Sidebar。
3. 若保留面板：确认侧栏/底栏仍能通过菜单/热键/API 打开；确认面板内部**仍有一个可用的标签切换入口**（否则视为功能回退，须在评估结论中标注）。
4. 若主菜单隐藏（`ui_menu_show:false`），确认仍有可用入口（命令面板/热键）打开面板。
5. Python：`app_proc(PROC_SHOW_SIDEBAR_GET, '')` 与 `PROC_SHOW_SIDEBAR_SET` 行为符合预期，且 `app_proc(PROC_SIDEPANEL_ENUM_ALL, '')` 不崩溃。
6. 内置插件：分别打开 Project / Tabs List / Snippet Panel，观察图标与按钮是否正常（若保留侧栏则必须全部正常）。
7. 全屏 / 免打扰切换不崩溃。

---

### 2.4 删除 Side panel（`AppPanels[TAppPanelId.Side]`，含 Code-Tree）

**界面位置**
- 主菜单 `View → Side panel`：`app/formmain.lfm:477-479`。
- 内容宿主：`PanelMain`（`formmain.lfm:103-116`）内的 `TAppPanelHost`，默认面板为 Code-Tree（`formmain.pas:3132`）。
- 面板工具栏 = `ToolbarSideTop`（在 Sidebar 内）。
- 标题栏 / 分隔条 /（可选）浮动窗口：`proc_panelhost.pas:148-170`。

**受影响的关联功能与依赖**
- **Code-Tree 整个功能**：`InitCodeTree`（`formmain.pas:2976-3053`）、`cmd_Tree*`（`formmain_cmd.inc:702-725`）、treehelper 系列（`app/treehelper_*.pas`）、定时刷新 `UpdateTreeByTimer`。
- **3 个内置插件**依赖侧栏面板 API：
  - `cuda_project_man`：`app/py/cuda_project_man/__init__.py:789,803,810,3599,3641,3994-3995`
  - `cuda_tabs_list`：`app/py/cuda_tabs_list/__init__.py:109,171`
  - `cuda_snippet_panel`：`app/py/cuda_snippet_panel/__init__.py:43-44`
- 插件事件 `TAppPyEvent.OnSidebarPopup`（`formmain_sidepanel.inc:178-183`）。
- 面板 Python 命令回调 `DoPyCommand(..., TATCommandInvoke.AppSidebar)`（`formmain_sidepanel.inc:140-149`）。
- 面板 API：`APP_PROC_SIDEPANEL_ACTIVATE/GET_CONTROL/ENUM_ALL/REMOVE/ADD_DIALOG/GET/SET_PROP/GET_IMAGELIST`（`proc_py_const.pas:358-365`）。
- 显隐 API：`APP_PROC_SHOW_SIDEPANEL_GET/SET`（`proc_py_const.pas:417-418`；实现 `formmain_py_api.inc:6134-6139`）。
- 会话/历史持久化：面板显隐、尺寸、最后标签、浮动位置（`formmain_loadsave.inc:144-173,355-367,1035-1054,1184-1185,1230-1254,1314-1339`）。
- 全屏 `p` 标志：`formmain.pas:7559`；窗口最小高度依赖底栏，见 `4115-4122`。
- 主题：面板标题颜色、分隔条颜色（`formmain_themes.inc:147-160`）。
- 本地化面板名：`proc_msg.pas:126-146,451-465`。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.pas` | 3128-3141, 3192, 4115-4122, 4489-4500, 4897-4900, 5225-5236, 7057-7058, 7388-7404, 7546-7559 | 宿主初始化、尺寸、显隐、勾选、全屏 |
| `app/formmain_cmd.inc` | 316-320, 408-443 | 切换/显示/隐藏/聚焦命令 |
| `app/formmain_updates_proc.inc` | 493-494, 994, 1273, 1741 | 启用禁用、`_Alt`、勾选、AddPanel |
| `app/proc_panelhost.pas` | 全文件 | 面板宿主核心 |
| `app/formmain_sidepanel.inc` | 全部 | 回调 |
| `app/formmain_bottompanel.inc` | 10-63 | 共用回调部分 |
| `app/formmain_py_api.inc` | 5517-5589, 5947-6055, 6134-6139, 6212-6220 | Python API |
| `app/formmain_loadsave.inc` | 见上 | 持久化 |
| `app/form_frame.pas` | 无直接依赖，但 Code-Tree 与编辑同步 | 树更新相关 |

**风险点（最高）**
- **删宿主而不删 API = 必崩**：`app_proc(PROC_SIDEPANEL_*)`、`PyHelper_EnumSidebar`、`DoSidebar_*` 大量直接解引用 `AppPanels[Side]`；必须先决定“保留一个空壳宿主”还是“移除常量并同步 Python 侧判断”。
- Code-Tree 是 CudaText 的导航核心之一；删除侧栏面板后 `cmd_Tree*`、treehelper、侧栏树过滤器、`@符号` 树跳转等都会失去 UI（后台逻辑可保留但无入口）。
- 3 个内置插件默认随发行版启用；不处理会导致插件初始化异常/控制台报错，可能影响启动时间与日志。
- 会话文件（`*.cuda-session`）与 `history.json` 中的 `tab_left:"Code-Tree"`、`size_side` 会失效，需要迁移或忽略。
- `UpdatePanels(msgPanelTree_Init, ...)` 在多处被调用（如 `cmd_ShowSidePanelAndSyntaxTree`、`DoSidebar_FocusCodetree`），删除后必须全部改为空实现或删除命令。
- 面板尺寸约束、分隔条缩放（`AppScaleSplitter`，`formmain.pas:5140`）需清理。

**删除后如何验证**
1. 全量构建（改了多个单元与 lfm，建议 `-B`）。
2. 启动无异常日志；`View` 菜单无 Side panel；命令面板无 “toggle side panel” 等命令。
3. `history.json` 中 `show_sidepanel:true`、`tab_left:Code-Tree`、`size_side` 存在时启动不崩溃。
4. 打开项目（`cuda_project_man`）、Tabs List、Snippet Panel，确认无 Python 异常；若插件未同步，应在控制台只看到“功能不可用”提示而不是堆栈。
5. 遍历 `cmd_Tree*` 热键/命令：不应崩溃；若保留命令，应优雅失败。
6. 全屏/免打扰、窗口缩放、最小尺寸约束正常。
7. Python：`app_proc(PROC_SIDEPANEL_ENUM_ALL,'')`、`PROC_SIDEPANEL_GET`、`PROC_SHOW_SIDEPANEL_GET/SET` 有明确返回值或明确异常策略（二选一，且与文档一致）。

---

### 2.5 删除 Bottom panel（`AppPanels[TAppPanelId.Btm]`，Console/Output/Validate）

**界面位置**
- 主菜单 `View → Bottom panel`：`app/formmain.lfm:480-482`。
- 面板按钮在 `ToolbarSideLow`（Sidebar 内）：`formmain_updates_proc.inc:1743-1745`。
- 内容：`fmConsole`（`app/form_console.pas`）、`fmOutput`、`fmValidate`（`formmain.pas:3201-3207`）。

**受影响的关联功能与依赖**
- Python 运行输出 / 错误输出（控制台）。
- `app_log` API（`formmain_py_api.inc:3016-3069`）：`LOG_ADD/LOG_CLEAR` 及 `LOG_SET_*` 系列（正则/行号/文件名等）直接作用于 `fmOutput/fmValidate`；`LOG_CONSOLE_*` 作用于控制台。
- 命令：`ShowPanelConsole/Output/Validate`、`ShowPanel*_AndFocus`、`ShowPanelBottomAndFocus`、`HideBottomPanel`（`formmain_cmd.inc:376-443`）。
- 控制台交互：补全、历史、数字跳转、Escape 关闭（`formmain.pas:4025`、`form_console.pas:365`）。
- 查找按钮：`DoBottom_FindClick`（`formmain_bottompanel.inc:21-35`）——它只是打开 Find 对话框，不依赖面板本体，但挂在侧栏 `ToolbarSideMid`。
- 焦点判断 `IsFocusedBottom`（`formmain_bottompanel.inc:10-18`）与 `formmain.pas:7952,10666-10669`。
- 词切换/自动补全快捷键：`fmConsole.ShortCutForAutoCompletion`（`formmain.pas:5202,6038-6039`）。
- 角标（错误数/输出行数）：`formmain.pas:3803-3834`。
- 会话/历史：`show_bottom`、`float_bottom`、`size_bottom`、`tab_bottom`、`panels/bottom_*`。
- Python API：`PROC_BOTTOMPANEL_ACTIVATE/GET_CONTROL/REMOVE/ADD_DIALOG/GET/SET_PROP/ENUM_ALL`（`proc_py_const.pas:402-408`）、`PROC_SHOW_BOTTOMPANEL_GET/SET`（419-420）。
- 全屏 `b` 标志：`formmain.pas:7557`。
- 主题/字体：输出面板字体 `cmd_OpsFontOutput`、`ui_console_wrap`。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.pas` | 3143-3156, 3193, 3201-3207, 3803-3834, 4025, 4115-4122, 4489-4500, 5141, 5205-5210, 7355-7359, 7406-7422, 7449-7475, 7557 | 宿主、初始化、交互、显隐、命令实现 |
| `app/formmain_cmd.inc` | 321-325, 367-371, 376-411, 441-444 | 命令分发 |
| `app/formmain_bottompanel.inc` | 10-63 | 回调 |
| `app/form_console.pas` | 112, 425, 365 | 控制台窗体 |
| `app/formmain_py_api.inc` | 3016-3069, 5998-6055, 6144-6149, 6214-6229 | `app_log` / 面板 API |
| `app/proc_panelhost.pas` | 全文件 | 宿主核心 |
| `app/formmain_loadsave.inc` | 144-173, 355-367, 1035-1054, 1230-1254 | 持久化 |
| `app/proc_globdata.pas` | 271/2326 等 | 面板相关配置 |
| `app/formmain_themes.inc` | 147-160, 203-207 | 主题/控制台主题 |
| `app/settings_default/default.json` | 1696-1698, 1741-1745 | `ui_console_wrap`、`ui_bottom_on_start` |
| `app/py/cuda_addonman/*` | 输出依赖 | 安装/升级日志返回输出面板（需回归） |

**风险点（最高）**
- 删除面板会让 `app_log` 无处可写；若不改 API，`fmOutput/fmValidate` 为 nil 时可能 AV（当前有 nil 检查，但需要审计所有调用点）。
- Python 插件的 `print()` / 异常信息默认进控制台；删除后工程师排障能力显著下降，需要提供替代（日志文件/外部终端）。
- `cuda_addonman` 的安装/升级过程、`check_cudatext_updates` 的用户反馈依赖输出/控制台。
- 侧栏 `ToolbarSideLow` 的三个按钮失去宿主逻辑；若同时删 Sidebar，则 `DoBottom_FindClick` 的按钮也一并消失（Find 仍可由菜单/热键打开）。
- 大量 `fmConsole` 引用（约 40 处）需要逐项判断；`EscapeCloseConsole`、`IsFocusedBottom`、`DoShowBottomAndFocus` 等行为需重新定义。
- 会话/历史键失效；窗口 `Constraints.MinHeight` 依赖底栏尺寸（`formmain.pas:4119-4122`）。

**删除后如何验证**
1. 构建并启动；`View` 菜单无 Bottom panel。
2. 触发 Python 脚本 `print(...)`、抛出异常、`app_log(LOG_ADD, ...)`：不崩溃、有明确替代输出（控制台或日志文件）。
3. 打开 Find/Replace（菜单与侧栏按钮若保留）：正常。
4. 运行 `Addons Manager` 一次安装/升级流程：无异常。
5. `history.json` 含 `show_bottom:true`/`float_bottom`/`tab_bottom:"Console"` 时启动正常。
6. 全屏/免打扰切换、窗口缩放到最小尺寸正常。
7. Python：`PROC_BOTTOMPANEL_*`、`PROC_SHOW_BOTTOMPANEL_*` 行为符合既定策略（优雅失败或已删除常量）。

---

### 2.6 删除 Floating side panel（浮动侧栏面板）

**界面位置**
- 主菜单 `View → Floating side panel`：`app/formmain.lfm:483-485`。
- 只有菜单/命令入口，无工具栏按钮；关闭浮动窗时菜单勾选由 `formmain_sidepanel.inc:156-159` 复位。

**受影响的关联功能与依赖**
- `TAppPanelHost.Floating` 与其浮动 `TForm`：`proc_panelhost.pas:57-63,76-77,85-89,174-221,294-297,527-540`。
- 面板从 `PanelRoot` 迁移到 `FormFloat` 时的尺寸/对齐/标题逻辑：`proc_panelhost.pas:148-170,180-234,615-640`。
- 焦点逻辑专门处理浮动窗口：`formmain_sidepanel.inc:68-111`（Code-Tree 过滤器/树聚焦）。
- 保存/恢复：`formmain_loadsave.inc:144-148`（`/pos/side`）、`161`（`float_side`）、`1251`；`formmain.pas:3192`（默认浮动矩形）。
- Python API：`APP_PROC_FLOAT_SIDE_GET/SET`（`proc_py_const.pas:434-435`；`formmain_py_api.inc:6212-6220`）。
- GTK2 特判：`proc_panelhost.pas:192-195`（GTK2 下浮动直接 no-op）。
- **当前运行状态**：`app/bin/windows-amd64/settings/history.json:12` 已是 `"float_side": true`，第 7 行还有 `/pos/side`。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.lfm` | 483-485 | 菜单项 |
| `app/formmain.pas` | 386, 687, 3192, 7349-7353 | 字段、`_Alt`、默认矩形、切换实现 |
| `app/formmain_cmd.inc` | 361-365 | 命令分发 |
| `app/formmain_updates_proc.inc` | 996, 1139, 1275 | `_Alt`、热键、勾选 |
| `app/proc_panelhost.pas` | 见上 | 浮动实现 |
| `app/formmain_sidepanel.inc` | 77-82, 100-107, 156-159 | 浮动焦点与关闭回调 |
| `app/formmain_loadsave.inc` | 144-148, 161, 1184, 1251 | 位置与状态持久化 |
| `app/formmain_py_api.inc` | 6212-6220 | Python API |
| `app/formmain_translation.inc` | 279 | 文案 |
| `translation template.ini` | 147 | `t_fl_s` |

**风险点**
- **状态迁移**：若只删 UI，不改读写逻辑，`float_side:true` 会继续把面板放进浮动窗；若删 `Floating` 实现但保留读取，会编译失败或面板“消失”。必须显式忽略旧键并把 `Floating` 固定为 `false`。
- 浮动窗口是 `fsStayOnTop`、`ShowInTaskBar=stNever`（`proc_panelhost.pas:531-539`），删除后不再有“脱离主窗口”的用法。
- 多显示器/位置恢复代码（`/pos/side`）与 `DoOps_LoadFormRect` 需清理。
- GTK2 分支可一并删除，但非 Windows 平台需回归（Linux/macOS 构建配置）。
- 关闭浮动窗回调会更新菜单勾选；删菜单项后该回调要删或改为空，否则引用不存在的 `mnuViewSide`。

**删除后如何验证**
1. 构建/启动，菜单无 Floating side panel。
2. 用当前 `history.json`（`float_side:true`）直接启动：面板不浮动、不丢失、不崩溃。
3. 打开/关闭侧栏面板，标题、尺寸、分隔条正常。
4. Code-Tree 过滤器聚焦（菜单命令/热键）在浮动被禁用后仍工作。
5. 全屏/免打扰切换、主窗口移动/多显示器正常。
6. Python：`PROC_FLOAT_SIDE_GET` 恒为 False；`PROC_FLOAT_SIDE_SET true` 不应创建窗口（且返回策略明确）。

---

### 2.7 删除 Floating bottom panel（浮动底栏面板）

与 2.6 高度对称，差异点如下：

**界面位置**：`app/formmain.lfm:486-488`；关闭浮动回调 `formmain_bottompanel.inc:60-63`。

**后台代码范围**
- `app/formmain.pas:387,688,3193,7355-7359`（字段、`_Alt`、默认矩形、切换）。
- `app/formmain_updates_proc.inc:997,1140,1276`（`_Alt`、热键、勾选）。
- `app/formmain_loadsave.inc:147-148,162,1185,1252`（`/pos/bottom`、`float_bottom`）。
- `app/formmain_py_api.inc:6222-6230`；`proc_py_const.pas:436-437`。
- `translation template.ini:148`（`t_fl_b`）。
- 当前运行时 `history.json:13` 为 `"float_bottom": false`，第 7 行有 `/pos/bottom`。

**额外风险**
- 底栏浮动时，`FormFloat` 内承载 Console/Output/Validate；删除浮动不影响不浮动路径，但如果第 5 项（Bottom panel）也删，则两者一起删时需保证 `FormFloat` 相关的所有引用先清理干净（`proc_panelhost.pas` 的字段会被两处删除共用）。
- 关闭浮动窗回调 `DoBottom_OnCloseFloatForm` 会把 `mnuViewBottom` 勾选复位（`formmain_bottompanel.inc:60-63`）；删除浮动功能后该回调需删除或改为空，删除底栏菜单项时也要同步处理。

**验证**：同 2.6，把 `float_side` 换成 `float_bottom`，并使用 `float_bottom:true` 的历史文件启动验证。

---

### 2.8 删除 Help 菜单下的 Forum / Wiki / Report an issue / Check for updates...

**界面位置**
- `app/formmain.lfm:645-665`：
  - `mnuHelpForum`（647-649）
  - `mnuHelpWiki`（650-652）
  - `mnuHelpIssues`（653-655）
  - `mnuHelpCheckUpd`（656-658）
  - `mnuHelpSep2`（659-661，删除 4 项后将成为**开头分隔符**）
  - `mnuHelpAbout`（662-664，保留）

**受影响的关联功能与依赖**
- 命令码：`cmd_HelpForum=2701`、`cmd_HelpWiki=2702`、`cmd_HelpIssues=2706`、`cmd_HelpCheckUpdates=2708`（`proc_cmd.pas:271-275`）。
- 热键/命令面板注册：`proc_cmd.pas:817-820`（只注册 About/Forum/Wiki/Issues，**Check for updates 未注册**）。
- 命令分发：`formmain_cmd.inc:799-812`。
- 实现：`DoHelpForum`（`formmain.pas:5050-5053`，旧 SourceForge 论坛）、`DoHelpWiki`（`8531-8534`）、`DoHelpIssues`（`8808-8811`）。
- Check for updates 依赖：`UiOps.AllowProgramUpdates`（`proc_globdata.pas:425,2288`）+ 内置插件 `cuda_addonman.check_cudatext_updates`（`app/py/cuda_addonman/__init__.py:851-853`），且 `mnuHelpCheckUpd.Enabled` 在 `FormCreate` 设置（`formmain.pas:3123`）。
- 菜单 ID API：`PyMenuId_TopHelp = 'top-help'`（`proc_py_const.pas:657`，`formmain_py_api.inc:458`）——**父菜单必须保留**。
- 本地化：`formmain_translation.inc:323-330`（含 `DoMenuitemEllipsis(mnuHelpCheckUpd)`）。
- 命令分类列表：`proc_cmd.pas:961-964`（`IsCommandNeedTimer`）。
- 更新入口仍有备用：`Plugins → Addons Manager → Check for CudaText updates`（`app/py/cuda_addonman/install.inf:44-45`）。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.lfm` | 645-665 | 菜单项与分隔符 |
| `app/formmain.pas` | 426-432, 3123, 5050-5053, 8531-8534, 8808-8811, 3230 | 字段、启用状态、URL 实现、菜单 hint |
| `app/formmain_cmd.inc` | 799-812 | 命令分发 |
| `app/formmain_updates_proc.inc` | 1018, 1164-1167 | `mnuApple_About`、热键 |
| `app/proc_cmd.pas` | 271-275, 817-820, 961-964 | 命令码、注册、分类 |
| `app/formmain_translation.inc` | 323-330 | 本地化 |
| `app/data/lang/translation template.ini` | 188-193 | `fo/wi/iss/chk` 键 |
| `app/py/cuda_addonman` | `install.inf:44-45` | 更新功能的备用入口（保留） |

**风险点**
- 删除 4 条后必须处理 `mnuHelpSep2`，否则 Help 菜单以分隔线开头（视觉缺陷）。
- 若删除 `cmd_Help*` 常量，`IsCommandNeedTimer` 与 `M.Add` 必须同步，否则编译失败；若只删菜单，命令面板仍可执行这些 URL（入口未真正消失）。
- `PyMenuId_TopHelp` 必须保留；第三方插件可能向 Help 菜单添加项（`menu_proc('top-help', MENU_ADD, ...)`），删父菜单会导致插件加项失败（当前内置插件未使用，但属于公开 API）。
- `Check for updates` 删除后，程序更新入口仅剩 Addons Manager，需在发布说明中明确。
- `DoHelpCheckUpdates` 依赖内置插件；若用户卸载 `cuda_addonman`，原菜单项本就不会有实际效果（删除不引入新问题）。

**删除后如何验证**
1. 构建/启动；Help 菜单只剩 `About...`（且首项不是分隔符）。
2. 命令面板与热键对话框无 `help: forum/wiki/issues`；若保留 `cmd_HelpCheckUpdates` 则其分发路径行为明确。
3. 用 Python `menu_proc('top-help', MENU_ADD, command=0, caption='Test')` 添加临时项：Help 菜单出现该项（证明父菜单与 API 未被破坏）。
4. `Plugins → Addons Manager → Check for CudaText updates` 仍可使用（联网场景）。
5. 关于对话框（About）正常，macOS 的 App 菜单 About 正常（`formmain_updates_proc.inc:1018`）。

---

### 2.9 删除 Split 菜单及其全部子项

**界面位置**
- 顶层菜单 `Sp&lit`：`app/formmain.lfm:572-644`，含：
  - `Don't split tab` / `Split tab vertically` / `Split tab horizontally`（单选项，574-588）
  - 分隔符 `mnuSplitSep`（589-591）
  - 13 个分组单选项 `One group / 2 vert / 2 horz / 3 vert / 3 horz / 1+2 vert / 1+2 horz / 4 vert / 4 horz / 4 grid / 6 vert / 6 horz / 6 grid`（592-643）

**受影响的关联功能与依赖**
- 命令：`cmd_SplitTab*`（2617-2626）、`cmd_Groups*`（2627-2639）（`proc_cmd.pas:184-207`）。
- 命令注册：`proc_cmd.pas:648-657`。
- 命令分发：`formmain_cmd.inc:526-551`（分组切换 `UpdateGroupsMode`）、`1117-1205`（分屏 `Frame.Splitted/SplitHorz`）。
- 勾选逻辑：`UpdateMenuChecks_FrameSplit`（`formmain_updates_proc.inc:1294-1300`），在 `formmain.pas:2675,11053` 与 `formmain_cmd.inc:1122-1165` 被调用。
- `_Alt` 记录：`proc_cmd` 之外的 `formmain.pas:690-705`、`formmain_updates_proc.inc:986-1012`。
- 菜单热键绑定：`formmain_updates_proc.inc:1108-1124`。
- 启用状态：`formmain_updates_proc.inc:1256-1261`（仅 3 个 Split 项）。
- **菜单顺序硬编码**：`formmain.pas:4327-4332` 使用 `MainMenu.Items[Count-2]=mnuSplit` 判断“标准菜单”；删除后条件恒为假，会走“自定义菜单”分支（`UpdateMenuItem_SetShortcutsRecursively`），需改成新的判断锚点（如 `mnuOp` / `mnuHelp`）。
- 菜单提示：`UpdateMenuItemHint(mnuSplit, 'top-groups')`（`formmain.pas:3231`）。
- Python 菜单 ID：`PyMenuId_TopGroups='top-groups'` → `mnuSplit`（`formmain_py_api.inc:459`；`proc_py_const.pas:658`）。第三方插件可能向该菜单添加项；删除后 `menu_proc` 会返回空 id（`DoMenuAdd_Params` 对 nil 安全，不崩溃）。
- 本地化：`formmain_translation.inc:250-262`（分组项）、`318-321`（Split 项）。
- 真正实现分屏/分组的后端在外部 `TATGroups`（属 ATSynEdit 包）与 `TEditorFrame.Splitted/SplitHorz`；**只删菜单不会删除功能**，热键与命令仍可能触发。
- 其他入口：标签右键菜单 `mnuTabMoveF1..`、`formmain_tab_proc.inc:619-631`（浮动组）与 Split 菜单无关，**不要误删**。

**后台代码范围**

| 文件 | 位置 | 内容 |
|------|------|------|
| `app/formmain.lfm` | 572-644 | 全部菜单项 |
| `app/formmain.pas` | 272-276, 433-445, 690-705, 3231, 4320-4338 | 字段、`_Alt`、hint、菜单顺序判断 |
| `app/formmain_updates_proc.inc` | 986-1012, 1108-1124, 1256-1261, 1279-1299 | `_Alt`、热键、启用、勾选 |
| `app/formmain_cmd.inc` | 526-551, 1117-1205 | 命令分发 |
| `app/proc_cmd.pas` | 184-207, 648-657, 824-970, 1017+ | 命令码、注册、分类列表 |
| `app/formmain_py_api.inc` | 459 | `top-groups` 映射 |
| `app/proc_py_const.pas` | 658 | Python 菜单 ID |
| `app/formmain_translation.inc` | 250-262, 318-321 | 本地化 |
| `app/data/lang/translation template.ini` | 116-121 | `sp_*/g1` 等键 |
| `app/py/cudatext.py` | 无 `top-groups` 常量（按字符串使用） | 插件按字符串调用 |

**风险点**
- 若只删菜单：所有 Split 命令仍在命令面板/热键中可用，功能没有真正“去掉”，与用户预期可能不符。
- 若删命令与常量：必须同步 `M.Add`、`IsCommandNeedTimer`/`IsCommandForMacros`、`formmain_cmd.inc` 分发、`UpdateMenuChecks_FrameSplit` 及其调用点，否则编译失败或留下悬空调用。
- `MainMenu.Items[Count-2]=mnuSplit` 的硬编码判断必须改，否则每次启动都会走自定义菜单的快捷键递归分支（功能一般无害，但属于行为变化与性能浪费）。
- `PyMenuId_TopGroups` 若不删而映射为 nil：第三方插件加项会静默失败（返回空 id），需要在文档中注明；若删常量，插件字符串调用同样失败但不会崩溃。
- 分隔符/单选项 `GroupIndex` 删除后无影响；但 `mnuSplitSep` 与后续 `mnuGr*` 必须整组删除，避免孤立分隔符。
- 与“编辑器浮动组（Floating 1/2/3，`mnuTabMoveF*`）”是两套不同功能，**Split 菜单删除不应波及它们**。

**删除后如何验证**
1. 构建/启动；顶层菜单无 Split，Help 紧接 Options。
2. 命令面板/热键对话框无 `split tab:*`、`groups:*` 项（若按“只删菜单”方案，则确认它们仍存在并在报告中说明）。
3. 用热键触发原 Split 命令（若命令已删，应无反应且不报错）。
4. 打开多个标签、侧栏面板、浮动组，确认标签右键菜单和“浮动 1/2/3”不受影响。
5. `Menu.Items[Count-1]` 为 Help；确认启动时仍按“标准菜单”分支处理（或已改用新的判断锚点后，行为与改动前一致）。
6. Python `menu_proc('top-groups', MENU_ADD, ...)` 行为明确（空 id/异常/已删除常量三者选一，并与文档一致）。

---

## 3. 跨项共享改动清单（实施时按此表核对）

| 共享点 | 涉及项 | 文件 |
|--------|--------|------|
| 顶层菜单顺序判断 `Items[Count-2]=mnuSplit` | 9 | `app/formmain.pas:4320-4338` |
| 主菜单字段与 `*_Alt` 记录 | 1,2,3,4,5,6,7,8,9 | `app/formmain.pas:272-445, 677-705`；`formmain_updates_proc.inc:963-1014` |
| `UpdateMenuHotkeys` / `UpdateMenuChecks` | 全部 | `formmain_updates_proc.inc:1016-1300` |
| 命令码 / `M.Add` / 分类列表 | 1,2,4,5,6,7,9 | `app/proc_cmd.pas` |
| 命令分发 `DoCommand` | 1,2,4,5,6,7,8,9 | `app/formmain_cmd.inc` |
| 面板宿主核心 | 3,4,5,6,7 | `app/proc_panelhost.pas` |
| 面板 Python API | 3,4,5,6,7 | `app/formmain_py_api.inc` |
| Python 常量 | 1,2,3,4,5,6,7 | `proc_py_const.pas`、`py/cudatext.py`、`py/cudax_lib.py` |
| 配置默认值与读写 | 1,2,3,4,5,6,7 | `settings_default/default.json`、`proc_globdata.pas`、`formmain_loadsave.inc` |
| 主题色 | 1,2,3,4,5 | `proc_colors.pas`、`data/themes/*.cuda-theme-ui` |
| 本地化 | 1,2,3,4,5,6,7,8,9 | `formmain_translation.inc`、`translation template.ini` |
| 构建单元引用 | 2（若删单元） | `app/cudatext.lpr`、`app/cudatext.lpi` |
| 运行副本同步 | 全部 | `app/bin/windows-amd64/{py,data,settings_default}`、`app/cudatext.app/Contents/Resources/...` |
| 随附插件 | 4,5 | `app/py/cuda_project_man`、`cuda_tabs_list`、`cuda_snippet_panel`、`cuda_addonman` |

---

## 4. 两种实施深度（供决策）

### 方案 A：仅“隐藏入口”（低风险，推荐用于 1/6/7）
- 删除菜单项/命令/热键，保留后台字段与 Python API，强制功能不可见（例如 `OptMinimapVisible:=false`、`Floating` 恒为 `false`）。
- 优点：插件兼容、旧配置自动失效、回滚容易。
- 缺点：代码里仍有死功能；“去掉”不彻底；外部 ATSynEdit 仍会编译 Minimap。

### 方案 B：彻底删除（适用于 2/8/9，谨慎用于 3/4/5）
- 删除 UI、命令、配置、主题、API、单元引用与资源。
- 必须处理 0.2 的三个架构事实，并做状态迁移（`history.json` / `user.json` / 会话文件）。
- 缺点：改动面大、跨平台与插件回归成本高；对 4/5 会改变产品定位（失去 Code-Tree、Console 等核心能力）。

### 建议顺序
1. 先做 8（Help 条目）与 9（Split 菜单）——独立、易验证。
2. 再做 1/2（Minimap/Micromap）——先“隐藏入口”，决定是否改为 B。
3. 6/7（浮动）与 3（Sidebar）一起设计，因为 Sidebar 是面板按钮宿主。
4. 4/5（Side/Bottom panel）最后做，且必须先确定插件 API 策略（保留空壳 / 删除常量 + 同步插件）。

---

## 5. 通用回归验证清单

- [ ] 全量构建通过（`lazbuild app/cudatext.lpi --bm="windows x64"`；改 include/删单元时先清理 `app/lib/*.ppu` 或 `-B`）。
- [ ] 启动 `app\bin\windows-amd64\cudatext.exe`，无启动异常、无插件初始化堆栈。
- [ ] `View` 菜单与命令面板、热键对话框三者一致（无“菜单没有但命令仍可执行”的遗漏，除非刻意保留）。
- [ ] 旧配置兼容：`user.json`、`history.json`、会话文件含被删键时正常启动（不丢文件、不崩溃）。
- [ ] Python API：`app_proc` / 编辑器属性 / `menu_proc` 的失败路径明确且一致。
- [ ] 内置插件：Project / Tabs List / Snippet Panel / Addons Manager 至少启动与核心操作不报错。
- [ ] 交互：全屏、免打扰、窗口缩放、最小尺寸、分隔条拖动、标签切换、查找对话框。
- [ ] 检查 `app/bin/windows-amd64/cudatext_error.log` 与 Console 输出无新增异常。
- [ ] 同步运行副本：`app/bin/windows-amd64/{py,data,settings_default}` 与 macOS `Resources` 副本一致。
- [ ] 文档：`default.json` 注释、`readme/history.txt`、`wiki/` 中对应功能说明需更新（避免“文档仍宣称支持”）。

---

## 6. 备注：容易误删的相邻功能

| 名称相似但**不同**的功能 | 说明 |
|---|---|
| Floating groups（浮动编辑组 1/2/3） | `ShowFloatingForm1..3`、`GroupsFloating1..3`、标签右键“Floating 1/2/3”（`formmain.pas:652-667, 2354-2364`）。属于编辑器窗口分组，**不是**第 6/7 项的面板浮动 |
| Find/Replace 对话框 | 独立窗口（`form_find.pas`），侧栏的 Find 按钮只是打开它；删除 Sidebar 不等于删除查找功能 |
| 编辑器内通知面板 | `TEditorFrame.DoFocusNotificationPanel / DoHideNotificationPanels`（`form_frame.pas:5324,5360`），与 `AppPanels` 无关，不受第 3/4/5 项影响 |
| `mnuSelSplit`（选区分割） | `app/formmain.lfm:322`，与顶层 Split 菜单无关，勿删 |
| `SplitGroups`（分隔条颜色） | 主题色名，属于分组分隔条，不是菜单项 |
