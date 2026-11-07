# CudaText 界面 Token 说明

本文档对应 `app/data/themes/*.cuda-theme-ui` 中的 115 个界面颜色 Token。
目的：说明每个 Token 管什么、该用在哪、不该用在哪，避免改主题时"一对多"误伤。

> 本仓库只合并了由补丁生成的 `syn_wcag` / `sub_wcag` 派生主题与 `tools/theme_wcag/` 审计脚本，
> 原主题保持上游原值；历史安装版实验中的逐色值对照表未在本仓库保留。

---

## 1. Token 载体与生效方式

| 项 | 说明 |
|---|---|
| 载体 | `app/data/themes/<主题名>.cuda-theme-ui`，JSON，纯 `"键": "#RRGGBB"` |
| 数量 | 115 个键，8 套上游主题键名与行号完全一致（另有补丁生成的 `syn_wcag` / `sub_wcag`） |
| 空字符串 | 值为 `""` 表示**继承系统/上级设置**（如 `MenuFont`、`StatusBg`） |
| 生效 | 修改后重启 CudaText，或在设置中重新选择主题 |
| 当前主题 | `settings/user.json` 中 `ui_theme`；自动亮暗见 `ui_theme_auto_mode` |
| 默认亮/暗 | `ui_theme_light=syn`、`ui_theme_dark=sub`（`settings_default/default.json:904-908`） |

> 本仓库包含 Lazarus 工程（`app/cudatext.lpi`），核心外观相关源码可重新编译；但主题与图标的日常调整应优先通过本目录的 JSON 与 PNG 完成。

---

## 2. 判定规则

| 规则 | 阈值 | 适用范围 |
|---|---|---|
| 正文文字对比度 | ≥ 4.5:1 | 编辑器正文、行号、标签、列表、按钮、代码树、折行标记符号 |
| 非文本图形对比度 | ≥ 3:1 | 滚动条滑块、滚动条箭头、关闭叉号、内嵌下拉箭头、缩进参考线、括号连线、微缩图标记 |
| 状态阶梯 | disabled < passive < over < checked | 按钮、标签 |
| 层级阶梯 | 背景明度差 ≥ 3% | 页面底 / 面板 / 悬浮层 |

对比度按 WCAG 2.1 相对亮度公式计算。校验方法见第 4 节。

---

## 3. Token 分组说明表

### 3.1 编辑器文本

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `EdTextFont` | 正文文字色 | 唯一正文文字色 | 不要用于行号、标签、按钮 |
| `EdTextBg` | 正文背景 | 编辑器画布底色 | 不要用于弹层/面板背景 |
| `EdSelFont` | 选中文字色 | 文本选区内的字 | 不要用于"当前行高亮"的文字 |
| `EdSelBg` | 选中背景 | 文本选区底色 | 不要用于搜索结果高亮 |
| `EdDisableFont` | 只读区文字 | 只读文档、锁定区域 | 不要用于普通正文 |
| `EdDisableBg` | 只读区背景 | 只读文档底 | 不要用于普通画布 |
| `EdLinks` | 可点击链接 | 文档内 URL、路径 | 不要用于装饰性强调 |
| `EdLockedBg` | 锁定区域底 | 只读/锁定片段 | 不要用于选区 |
| `EdCarets` | 光标色 | 插入符；空值跟随正文 | 不要用于选中态 |
| `EdMarkers` | 标记色 | 书签/标记的指示块 | 不要用于正文强调 |
| `EdCurLineBg` | 当前行背景 | 光标所在行的整行底色 | 不要用于选中行（会与选区冲突） |
| `EdCurLineBg2` | 当前行次色 | 当前行需要第二色时（如渐变/叠加） | 单色主题下保持空字符串 |
| `EdIndentVLine` | 缩进参考线 | 显示缩进竖线时 | 不要用于代码块括号线（用 `EdBlockStaple`） |
| `EdUnprintFont` | 不可打印字符 | 空格点、行尾符等符号 | 不要期待高对比，本就是弱化元素 |
| `EdUnprintBg` | 不可打印字符底 | 通常与正文底相同 | 不要用于正文背景 |
| `EdUnprintHexFont` | 不可打印字符的十六进制 | 十六进制视图 | 不要用于正常符号 |
| `OtherTextFont` | 非编辑器文本 | 输出面板等非编辑文本 | 不要用于编辑器正文 |
| `OtherTextBg` | 非编辑器文本底 | 同上 | 不要用于编辑器画布 |

### 3.2 行号 / 标尺 / 边距 / 折行

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `EdGutterFont` | 行号文字 | 行号栏 | 不要用于正文；亮度应低于正文 |
| `EdGutterBg` | 行号栏背景 | 行号栏 | 不要用于编辑器画布 |
| `EdGutterCaretFont` | 当前行行号 | 高亮当前行号 | 不要用于所有行号（会失去焦点感） |
| `EdGutterCaretBg` | 当前行行号背景 | 当前行号格 | 不要用于整栏 |
| `EdRulerFont` | 标尺数字 | 列号标尺 | 不要用于行号 |
| `EdRulerBg` | 标尺背景 | 通常同行号栏 | 不要用于画布 |
| `EdFoldLine` | 折叠线（一级） | 折叠块左侧竖线 | 不要用于缩进线 |
| `EdFoldLine2` | 折叠线（二级） | 嵌套折叠 | 不要用于一级折线 |
| `EdFoldBg` | 折叠区背景 | 折叠后的占位块 | 不要用于普通行 |
| `EdFoldMarkLine` | 折行标记竖线 | 折行标记旁 | 不要用于标记本身 |
| `EdFoldMarkFont` | 折行标记符号 | 三角/加减号 | 不要用于文字 |
| `EdFoldMarkBorder` | 折行标记边框 | 标记框 | 不要用于画布边框 |
| `EdFoldMarkBg` | 折行标记背景 | 标记框底 | 不要用于 gutter 背景 |
| `EdMarginFixed` | 固定边距 | 固定列边距 | 不要用于光标边距 |
| `EdMarginCaret` | 光标边距 | 光标所在行边距 | 不要用于固定边距 |
| `EdMarginUser` | 用户边距 | 自定义边距标记 | 不要用于系统边距 |

### 3.3 选区 / 标记 / 编辑状态

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `EdBlockStaple` | 代码块括号连线 | 括号匹配连线 | 不要用于缩进线 |
| `EdBlockStapleActive` | 激活的括号连线 | 光标位于括号内时 | 不要用于普通连线；空值表示不区分 |
| `EdBlockSepLine` | 代码块分隔线 | 块之间分隔 | 不要用于行分隔 |
| `EdBookmarkBg` | 书签行背景 | 含书签的行 | 不要用于选区 |
| `EdBookmarkIcon` | 书签图标 | gutter 书签图标 | 不要用于按钮图标 |
| `EdMarkedRangeBg` | 标记范围背景 | 批量标记的区间 | 不要用于文本选区 |
| `EdStateChanged` | 已修改状态 | gutter 上的修改标记 | 不要用于文字前景 |
| `EdStateAdded` | 新增状态 | gutter 上的新增标记 | 不要用于文字前景 |
| `EdStateSaved` | 已保存状态 | gutter 上的保存标记 | 不要用于正文 |
| `EdComboArrow` | 内嵌下拉箭头 | 编辑器内的下拉控件 | 不要用于标签页箭头 |
| `EdComboArrowBg` | 内嵌下拉箭头背景 | 同上 | 不要用于画布 |
| `EdBorder` | 编辑器边框 | 未聚焦时的边框 | 不要用于聚焦态（用 `EdBorderFocused`） |
| `EdBorderFocused` | 聚焦边框 | 编辑器获得焦点 | 不要用于未聚焦态 |

### 3.4 标签页

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `TabBg` | 标签栏背景 | 标签栏空白区 | 不要用于激活标签底 |
| `TabFont` | 标签文字 | 所有标签 | 不要用于按钮文字 |
| `TabFontActive` | 激活标签文字 | 空值跟随 `TabFont` | 不要与 `TabFont` 差太多 |
| `TabFontMod` | 已修改标签文字 | 有未保存改动 | 不要用于普通标签 |
| `TabActive` | 激活标签底 | 当前标签 | 不要用于悬停态 |
| `TabActiveOthers` | 其他分组激活标签底 | 分屏时非焦点分组 | 不要用于单分组场景 |
| `TabPassive` | 非激活标签底 | 后台标签 | 不要用于激活标签 |
| `TabOver` | 悬停标签底 | 鼠标悬停 | 不要用于激活态 |
| `TabBorderActive` | 激活标签边框 | 当前标签上/下边 | 不要用于非激活标签 |
| `TabBorderPassive` | 非激活标签边框 | 后台标签分隔 | 不要用于激活标签 |
| `TabCloseBg` | 关闭按钮底 | 关闭按钮常态 | 空值表示透明 |
| `TabCloseBgOver` | 关闭按钮悬停底 | 悬停在关闭按钮 | 不要用于常态 |
| `TabCloseBorderOver` | 关闭按钮悬停边框 | 同上 | 不要用于常态 |
| `TabCloseX` | 关闭叉号 | 关闭按钮图标 | 不要用于独立按钮图标 |
| `TabCloseXOver` | 关闭叉号悬停 | 悬停时叉号色 | 不要用于常态 |
| `TabArrow` | 标签滚动箭头 | 标签过多时 | 不要用于下拉箭头 |
| `TabArrowOver` | 标签滚动箭头悬停 | 同上 | 不要用于常态 |
| `TabActiveMark` | 标签标记 | 标签上的状态点 | 不要用于文字 |
| `TabMarks` | 标签标记集 | 其他标记 | 不要用于背景 |

### 3.5 侧边栏与代码树

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `SideBg` | 侧边栏背景 | 侧栏空白区 | 不要用于代码树行背景 |
| `SideBadgeBg` | 侧栏徽标背景 | 数字角标 | 不要用于按钮 |
| `SideBadgeFont` | 侧栏徽标文字 | 数字角标文字 | 不要用于正文 |
| `TreeFont` | 树节点文字 | 代码树/文件树 | 不要用于列表 |
| `TreeBg` | 树背景 | 代码树区域 | 不要用于侧栏空白 |
| `TreeSelFont` | 树选中文字 | 选中节点 | 不要用于悬停态 |
| `TreeSelBg` | 树选中背景 | 选中节点底 | 不要用于悬停态 |
| `TreeSelBg2` | 树选中次级背景 | 非焦点分组的选中 | 不要用于主选中 |
| `TreeSign` | 树展开符 | 三角/加减号 | 不要用于图标 |

### 3.6 列表与自动补全

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `ListBg` | 列表背景 | 命令面板、补全列表 | 不要用于编辑器画布 |
| `ListSelBg` | 列表选中背景 | 选中项 | 不要用于悬停（无独立 token） |
| `ListFont` | 列表文字 | 列表所有项 | 不要用于树 |
| `ListSelFont` | 列表选中文字 | 选中项文字 | 不要用于常态 |
| `ListFontHotkey` | 快捷键提示 | 列表项右侧快捷键 | 不要用于主文字 |
| `ListFontHilite` | 高亮匹配 | 搜索/筛选命中文字 | 不要用于整行 |
| `ListCompletePrefix` | 补全已输入前缀 | 补全列表匹配部分 | 不要用于完整文字 |
| `ListCompleteParams` | 补全参数提示 | 函数签名提示 | 不要用于参数名 |

### 3.7 按钮

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `ButtonFont` | 按钮文字 | 所有按钮态 | 不要用于标签页 |
| `ButtonFontDisabled` | 禁用按钮文字 | 不可点击 | 允许低于 4.5（禁用态可弱化） |
| `ButtonBgPassive` | 按钮常态底 | 默认按钮 | 不要用于选中态 |
| `ButtonBgOver` | 按钮悬停底 | 鼠标悬停 | 不要用于常态；应比伪态更亮或更明显 |
| `ButtonBgChecked` | 按钮选中/按下底 | 切换按钮、按下态 | 不要与 `ButtonBgOver` 同值（会无法区分状态） |
| `ButtonBgDisabled` | 禁用按钮底 | 不可点击 | 不要与 `ButtonBgOver` 同值 |
| `ButtonBorderPassive` | 按钮常态边框 | 需要描边时 | 不要用高对比亮色（会抢视觉） |
| `ButtonBorderOver` | 按钮悬停边框 | 悬停强调 | 不要用纯红等警报色做悬停 |
| `ButtonBorderFocused` | 按钮聚焦边框 | 键盘焦点 | 不要用于常态 |

> 状态阶梯要求：`ButtonBgDisabled` < `ButtonBgPassive` < `ButtonBgOver`，`ButtonBgChecked` 需与前两者有可辨差异。

### 3.8 菜单与状态栏

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `MenuFont` | 菜单文字 | 顶部菜单；空值跟随系统 | 不要与 `ListFont` 混用 |
| `MenuFontHotkey` | 菜单快捷键 | 菜单右侧快捷键 | 不要用于菜单主文字 |
| `MenuFontDisabled` | 禁用菜单项 | 不可用菜单 | 不要用于普通菜单项 |
| `MenuBg` | 菜单背景 | 空值跟随系统 | 不要用于列表背景 |
| `MenuSelBg` | 菜单选中背景 | 高亮菜单项 | 不要用于列表选中 |
| `StatusFont` | 状态栏文字 | 底部状态栏；空值跟随系统 | 不要用于正文 |
| `StatusBg` | 状态栏背景 | 空值跟随系统 | 不要用于侧栏 |

### 3.9 滚动条 / 分隔条 / 迷你地图

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `ScrollBack` | 滚动条槽底 | 滚动轨道 | 不要用于滑块 |
| `ScrollRect` | 滚动条背景块 | 轨道内层 | 不要用于滑块 |
| `ScrollFill` | 滚动条滑块 | 可拖动部分 | 不要用于轨道 |
| `ScrollArrow` | 滚动条箭头 | 两端箭头 | 不要用于滑块 |
| `ScrollScrolled` | 已滚动区域 | 轨道中已过部分 | 不要用于滑块 |
| `SplitMain` | 主分隔条 | 主分屏之间 | 不要用于分组内分隔 |
| `SplitGroups` | 分组分隔条 | 分组内分屏 | 不要用于主分隔 |
| `EdMinimapBorder` | 迷你地图边框 | 迷你地图外框 | 不要用高对比色 |
| `EdMinimapTooltipBg` | 迷你地图提示背景 | 悬停提示 | 不要用于面板 |
| `EdMinimapTooltipBorder` | 迷你地图提示边框 | 同上 | 不要用于面板边框 |
| `EdMicromapBg` | 微缩图背景 | 微缩图区域 | 不要用于迷你地图 |
| `EdMicromapViewBg` | 当前视口块 | 微缩图中的可视范围 | 不要用于背景 |
| `EdMicromapOccur` | 搜索结果点 | 微缩图中的命中点 | 不要用于视口 |
| `EdMicromapSpell` | 拼写错误点 | 微缩图中的拼写错误 | 不要用于命中点 |

### 3.10 导出

| Token | 用途 | 使用场景 | 禁用场景 |
|---|---|---|---|
| `ExportHtmlBg` | 导出 HTML 背景 | HTML 导出 | 不要用于应用界面 |
| `ExportHtmlNumbers` | 导出 HTML 行号 | HTML 导出 | 不要用于应用界面 |

---

## 4. 派生主题与校验

本仓库的 8 套上游主题保持原值不动；`syn_wcag` / `sub_wcag` 是 `tools/theme_wcag/apply_patches.py`
按修正建议生成的副本，只改色值，不改键名与顺序。

1. **审计**：`python tools/theme_wcag/audit_contrast.py` 扫描 `app/data/themes/*.cuda-theme-ui`，
   按第 2 节的组合与阈值计算对比度，写出 `tools/theme_wcag/theme_contrast_report.md` 与
   `theme_patches.json`。
2. **人工覆盖**：`theme_overrides.json` 用于调整自动建议——值为颜色表示强制采用，值为 `null`
   表示撤销该条建议、保留源主题原值。
3. **生成**：`python tools/theme_wcag/apply_patches.py <主题名>`，只新增 `<主题名>_wcag` 副本。
4. **校验 JSON**：`Get-Content <file> -Raw | ConvertFrom-Json`。
5. **看实际效果**：重启 CudaText 后切换主题确认。

约束：

- 不要给 `MenuFont` / `MenuBg` / `StatusFont` / `StatusBg` 填值，除非确实要覆盖系统主题
- 优先使用 `tools/theme_wcag/apply_patches.py` 生成 `*_wcag` 副本，不要直接改上游主题原文件
- 不要修改 `app/py/cuda_palette/__init__.py` 里的颜色，那是调色板数据，不是界面 Token

---

## 6. 修改与校验流程

1. **备份**：`Copy-Item app/data/themes app/data/themes.bak-<日期> -Recurse`
2. **改值**：只改 `"键": "#RRGGBB"` 的色值，不改键名、不改顺序
3. **校验 JSON**：`Get-Content <file> -Raw | ConvertFrom-Json`
4. **校验对比度**：按 WCAG 公式计算前景/背景组合，正文 ≥4.5、图形 ≥3
5. **校验灰阶**：纯灰值应只落在第 5 节的 8 级 + 例外值内
6. **看实际效果**：重启 CudaText 后切换主题确认
7. **回滚**：用备份目录覆盖

约束：

- 不要给 `MenuFont` / `MenuBg` / `StatusFont` / `StatusBg` 填值，除非确实要覆盖系统主题
- 优先使用 `tools/theme_wcag/apply_patches.py` 生成 `*_wcag` 副本，不要直接改上游主题原文件
- 不要修改 `app/py/cuda_palette/__init__.py` 里的颜色，那是调色板数据，不是界面 Token
