# CudaText UI 主题对比度审计报告

依据：doc/DESIGN-TOKENS.md 第 2 节判定规则；WCAG 2.1 相对亮度公式。
审计对象：8 套 UI 主题 × 34 组前景/背景配对。

> **口径说明**：本报告由 `tools/theme_wcag/audit_contrast.py` 生成，
> 只审计基主题（`app/data/themes/` 下除 `*_wcag` 之外的 UI 主题）；
> `*_wcag` 是 `apply_patches.py` 的生成物，不参与审计。

> **应用前必读**：建议值只保证「对比度达标」，不保证满足 DESIGN-TOKENS.md 第 5 节灰阶规范。
> 图形类（缩进线、括号连线、滚动条滑块）与禁用态属于刻意弱化的视觉元素，
> 是否强制拉到 3:1 应人工判断；强行拉高可能让辅助线抢走正文注意力。

## 汇总

| 项 | 数量 |
|---|---|
| 有效配对 | 232 |
| 未达标 | 96 |
| 其中需修正（不含弱化元素） | 93 |
| 已给出自动修正建议 | 93 |

> 空值 Token（如 MenuFont / StatusBg）表示继承系统主题，无法静态计算，已跳过。
> `weak` 类（不可打印字符）为刻意弱化，仅报告不建议改。

## 按主题汇总

| 主题 | 有效配对 | 未达标 | 需修正 | 可自动修正 |
|---|---|---|---|---|
| amy | 29 | 7 | 6 | 6 |
| cobalt | 29 | 9 | 9 | 9 |
| darkwolf | 29 | 11 | 11 | 11 |
| ebony | 29 | 16 | 15 | 15 |
| green | 29 | 16 | 16 | 16 |
| navy | 29 | 12 | 12 | 12 |
| sub | 29 | 15 | 15 | 15 |
| syn | 29 | 10 | 9 | 9 |

## 未达标明细（需修正项）

| 主题 | 部位 | 前景 Token | 现值 | 背景 Token | 背景值 | 实测 | 要求 | 建议值 | 建议后 |
|---|---|---|---|---|---|---|---|---|---|
| amy | 代码块括号连线 | `EdBlockStaple` | #3A1F41 | `EdTextBg` | #200020 | 1.34 | 3.0 | #606060 | 3.09 |
| amy | 列表快捷键提示 | `ListFontHotkey` | #78688F | `ListBg` | #200020 | 3.86 | 4.5 | #817591 | 4.52 |
| amy | 当前行行号 | `EdGutterCaretFont` | #78688F | `EdGutterCaretBg` | #320018 | 3.63 | 4.5 | #847C8F | 4.58 |
| amy | 标尺数字 | `EdRulerFont` | #78688F | `EdRulerBg` | #200020 | 3.86 | 4.5 | #817591 | 4.52 |
| amy | 滚动条滑块 | `ScrollFill` | #340A34 | `ScrollBack` | #290529 | 1.08 | 3.0 | #646464 | 3.09 |
| amy | 行号 | `EdGutterFont` | #78688F | `EdGutterBg` | #200020 | 3.86 | 4.5 | #817591 | 4.52 |
| cobalt | 代码块括号连线 | `EdBlockStaple` | #26435C | `EdTextBg` | #002240 | 1.57 | 3.0 | #566E83 | 3.03 |
| cobalt | 内嵌下拉箭头 | `EdComboArrow` | #505050 | `EdComboArrowBg` | #001C35 | 2.14 | 3.0 | #676767 | 3.05 |
| cobalt | 列表快捷键提示 | `ListFontHotkey` | #00A0A0 | `ListBg` | #103050 | 4.19 | 4.5 | #00AAAA | 4.70 |
| cobalt | 微缩图命中点 | `EdMicromapOccur` | #5050C0 | `EdMicromapBg` | #002240 | 2.49 | 3.0 | #5F5FC5 | 3.02 |
| cobalt | 微缩图视口块 | `EdMicromapViewBg` | #103050 | `EdMicromapBg` | #002240 | 1.20 | 3.0 | #576D83 | 3.01 |
| cobalt | 文内链接 | `EdLinks` | #257181 | `EdTextBg` | #002240 | 2.88 | 4.5 | #3094A9 | 4.56 |
| cobalt | 滚动条滑块 | `ScrollFill` | #103050 | `ScrollBack` | #001C35 | 1.28 | 3.0 | #476B8E | 3.09 |
| cobalt | 滚动条箭头 | `ScrollArrow` | #505050 | `ScrollBack` | #001C35 | 2.14 | 3.0 | #676767 | 3.05 |
| cobalt | 选区文字 | `EdSelFont` | #D0D0D0 | `EdSelBg` | #86543A | 4.07 | 4.5 | #DDDDDD | 4.63 |
| darkwolf | 内嵌下拉箭头 | `EdComboArrow` | #808080 | `EdComboArrowBg` | #404E51 | 2.19 | 3.0 | #9A9A9A | 3.08 |
| darkwolf | 列表快捷键提示 | `ListFontHotkey` | #804080 | `ListBg` | #293134 | 1.87 | 4.5 | #989898 | 4.60 |
| darkwolf | 列表选中项 | `ListSelFont` | #89B4B1 | `ListSelBg` | #344A4B | 4.14 | 4.5 | #95BCB9 | 4.57 |
| darkwolf | 已修改标签文字 | `TabFontMod` | #FF0000 | `TabPassive` | #2D3429 | 3.21 | 4.5 | #FF6B6B | 4.63 |
| darkwolf | 微缩图命中点 | `EdMicromapOccur` | #5050C0 | `EdMicromapBg` | #404E51 | 1.34 | 3.0 | #9494C9 | 3.02 |
| darkwolf | 微缩图视口块 | `EdMicromapViewBg` | #808080 | `EdMicromapBg` | #404E51 | 2.19 | 3.0 | #9A9A9A | 3.08 |
| darkwolf | 文内链接 | `EdLinks` | #808000 | `EdTextBg` | #293134 | 3.16 | 4.5 | #9C9C0D | 4.53 |
| darkwolf | 标尺数字 | `EdRulerFont` | #808080 | `EdRulerBg` | #404E51 | 2.19 | 4.5 | #BBBBBB | 4.51 |
| darkwolf | 滚动条滑块 | `ScrollFill` | #404E51 | `ScrollBack` | #293134 | 1.53 | 3.0 | #667D81 | 3.04 |
| darkwolf | 行号 | `EdGutterFont` | #808080 | `EdGutterBg` | #404E51 | 2.19 | 4.5 | #BBBBBB | 4.51 |
| darkwolf | 补全参数提示 | `ListCompleteParams` | #4A7573 | `ListBg` | #293134 | 2.58 | 4.5 | #6AA19F | 4.55 |
| ebony | 代码块括号连线 | `EdBlockStaple` | #555555 | `EdTextBg` | #202020 | 2.19 | 3.0 | #6C6C6C | 3.10 |
| ebony | 代码树节点 | `TreeFont` | #858585 | `TreeBg` | #202020 | 4.42 | 4.5 | #888888 | 4.60 |
| ebony | 代码树选中节点 | `TreeSelFont` | #BBBBBB | `TreeSelBg` | #525252 | 4.07 | 4.5 | #C5C5C5 | 4.53 |
| ebony | 十六进制视图 | `EdUnprintHexFont` | #7C7C7C | `EdUnprintBg` | #242424 | 3.72 | 4.5 | #8B8B8B | 4.56 |
| ebony | 只读区文字 | `EdDisableFont` | #727272 | `EdDisableBg` | #151515 | 3.80 | 4.5 | #7F7F7F | 4.56 |
| ebony | 已修改标签文字 | `TabFontMod` | #E57124 | `TabPassive` | #383838 | 3.75 | 4.5 | #E98948 | 4.54 |
| ebony | 微缩图命中点 | `EdMicromapOccur` | #5050C0 | `EdMicromapBg` | #141414 | 2.85 | 3.0 | #5858C3 | 3.16 |
| ebony | 微缩图视口块 | `EdMicromapViewBg` | #303030 | `EdMicromapBg` | #141414 | 1.40 | 3.0 | #636363 | 3.07 |
| ebony | 折行标记符号 | `EdFoldMarkFont` | #707070 | `EdFoldMarkBg` | #242424 | 3.13 | 4.5 | #8C8C8C | 4.62 |
| ebony | 标尺数字 | `EdRulerFont` | #555555 | `EdRulerBg` | #202020 | 2.19 | 4.5 | #888888 | 4.60 |
| ebony | 滚动条滑块 | `ScrollFill` | #232323 | `ScrollBack` | #1C1C1C | 1.08 | 3.0 | #686868 | 3.06 |
| ebony | 禁用按钮（允许弱化） | `ButtonFontDisabled` | #404040 | `ButtonBgDisabled` | #303030 | 1.27 | 3.0 | #7B7B7B | 3.12 |
| ebony | 行号 | `EdGutterFont` | #505050 | `EdGutterBg` | #202020 | 2.02 | 4.5 | #888888 | 4.60 |
| ebony | 选区文字 | `EdSelFont` | #00AEFF | `EdSelBg` | #005272 | 3.47 | 4.5 | #52C8FF | 4.52 |
| ebony | 非激活标签文字 | `TabFont` | #999999 | `TabPassive` | #383838 | 4.12 | 4.5 | #A1A1A1 | 4.54 |
| green | 代码块括号连线 | `EdBlockStaple` | #A0A0A4 | `EdTextBg` | #E0E0E0 | 1.97 | 3.0 | #7F7F83 | 3.02 |
| green | 内嵌下拉箭头 | `EdComboArrow` | #80A0A0 | `EdComboArrowBg` | #AAC8C8 | 1.58 | 3.0 | #636C6C | 3.03 |
| green | 列表快捷键提示 | `ListFontHotkey` | #008080 | `ListBg` | #AAC8C8 | 2.68 | 4.5 | #075A5A | 4.51 |
| green | 列表选中项 | `ListSelFont` | #505050 | `ListSelBg` | #B0B0B0 | 3.72 | 4.5 | #434343 | 4.56 |
| green | 十六进制视图 | `EdUnprintHexFont` | #A0A0A4 | `EdUnprintBg` | #E0E0E0 | 1.97 | 4.5 | #636367 | 4.53 |
| green | 只读区文字 | `EdDisableFont` | #606060 | `EdDisableBg` | #DADADA | 4.50 | 4.5 | #5D5D5D | 4.71 |
| green | 已修改标签文字 | `TabFontMod` | #008080 | `TabPassive` | #C0C0C0 | 2.62 | 4.5 | #005757 | 4.62 |
| green | 当前行行号 | `EdGutterCaretFont` | #505050 | `EdGutterCaretBg` | #B0B0B0 | 3.72 | 4.5 | #434343 | 4.56 |
| green | 微缩图视口块 | `EdMicromapViewBg` | #C0C0C0 | `EdMicromapBg` | #E0E0E0 | 1.38 | 3.0 | #7E7E7E | 3.08 |
| green | 折行标记符号 | `EdFoldMarkFont` | #008080 | `EdFoldMarkBg` | #E0E0E0 | 3.62 | 4.5 | #006C6C | 4.73 |
| green | 滚动条滑块 | `ScrollFill` | #90A8A8 | `ScrollBack` | #AAC8C8 | 1.41 | 3.0 | #606D6D | 3.02 |
| green | 滚动条箭头 | `ScrollArrow` | #80A0A0 | `ScrollBack` | #AAC8C8 | 1.58 | 3.0 | #636C6C | 3.03 |
| green | 禁用按钮（允许弱化） | `ButtonFontDisabled` | #808080 | `ButtonBgDisabled` | #B0B0B0 | 1.82 | 3.0 | #5C5C5C | 3.08 |
| green | 缩进参考线 | `EdIndentVLine` | #A0A0A4 | `EdTextBg` | #E0E0E0 | 1.97 | 3.0 | #7F7F83 | 3.02 |
| green | 补全参数提示 | `ListCompleteParams` | #008080 | `ListBg` | #AAC8C8 | 2.68 | 4.5 | #075A5A | 4.51 |
| green | 非激活标签文字 | `TabFont` | #505050 | `TabPassive` | #C0C0C0 | 4.43 | 4.5 | #4D4D4D | 4.65 |
| navy | 代码块括号连线 | `EdBlockStaple` | #A0A0A4 | `EdTextBg` | #E0E0E0 | 1.97 | 3.0 | #7F7F83 | 3.02 |
| navy | 内嵌下拉箭头 | `EdComboArrow` | #8080C0 | `EdComboArrowBg` | #C0C0F0 | 2.09 | 3.0 | #6464A9 | 3.06 |
| navy | 列表快捷键提示 | `ListFontHotkey` | #505050 | `ListBg` | #A0A0E0 | 3.30 | 4.5 | #3C3C3C | 4.52 |
| navy | 十六进制视图 | `EdUnprintHexFont` | #A0A0A4 | `EdUnprintBg` | #E0E0E0 | 1.97 | 4.5 | #636367 | 4.53 |
| navy | 已修改标签文字 | `TabFontMod` | #0000FF | `TabPassive` | #B0B0B0 | 3.96 | 4.5 | #0000E6 | 4.52 |
| navy | 微缩图视口块 | `EdMicromapViewBg` | #C0C0C0 | `EdMicromapBg` | #E0E0E0 | 1.38 | 3.0 | #7E7E7E | 3.08 |
| navy | 折行标记符号 | `EdFoldMarkFont` | #8080E0 | `EdFoldMarkBg` | #E0E0E0 | 2.62 | 4.5 | #5555C9 | 4.51 |
| navy | 滚动条滑块 | `ScrollFill` | #C0C0F0 | `ScrollBack` | #A0A0E0 | 1.40 | 3.0 | #4747B2 | 3.06 |
| navy | 滚动条箭头 | `ScrollArrow` | #8080C0 | `ScrollBack` | #A0A0E0 | 1.49 | 3.0 | #4D4D9C | 3.01 |
| navy | 禁用按钮（允许弱化） | `ButtonFontDisabled` | #808080 | `ButtonBgDisabled` | #C0C0C0 | 2.17 | 3.0 | #696969 | 3.02 |
| navy | 缩进参考线 | `EdIndentVLine` | #A0A0A4 | `EdTextBg` | #E0E0E0 | 1.97 | 3.0 | #7F7F83 | 3.02 |
| navy | 补全参数提示 | `ListCompleteParams` | #505050 | `ListBg` | #A0A0E0 | 3.30 | 4.5 | #3C3C3C | 4.52 |
| sub | 代码块括号连线 | `EdBlockStaple` | #505050 | `EdTextBg` | #272822 | 1.84 | 3.0 | #717171 | 3.05 |
| sub | 代码树选中节点 | `TreeSelFont` | #B0B0B0 | `TreeSelBg` | #505050 | 3.72 | 4.5 | #C2C2C2 | 4.53 |
| sub | 内嵌下拉箭头 | `EdComboArrow` | #505050 | `EdComboArrowBg` | #171814 | 2.21 | 3.0 | #646464 | 3.01 |
| sub | 列表快捷键提示 | `ListFontHotkey` | #80A0D0 | `ListBg` | #404040 | 3.88 | 4.5 | #93AED7 | 4.58 |
| sub | 列表选中项 | `ListSelFont` | #B0B0B0 | `ListSelBg` | #606060 | 2.90 | 4.5 | #DBDBDB | 4.54 |
| sub | 当前行行号 | `EdGutterCaretFont` | #808080 | `EdGutterCaretBg` | #39382E | 2.99 | 4.5 | #A1A1A1 | 4.57 |
| sub | 微缩图命中点 | `EdMicromapOccur` | #5050C0 | `EdMicromapBg` | #272822 | 2.30 | 3.0 | #6666C8 | 3.04 |
| sub | 微缩图视口块 | `EdMicromapViewBg` | #39382E | `EdMicromapBg` | #272822 | 1.26 | 3.0 | #737160 | 3.02 |
| sub | 折行标记符号 | `EdFoldMarkFont` | #808080 | `EdFoldMarkBg` | #39382E | 2.99 | 4.5 | #A1A1A1 | 4.57 |
| sub | 文内链接 | `EdLinks` | #5050C0 | `EdTextBg` | #272822 | 2.30 | 4.5 | #8787CB | 4.50 |
| sub | 标尺数字 | `EdRulerFont` | #808080 | `EdRulerBg` | #272822 | 3.76 | 4.5 | #8F8F8F | 4.60 |
| sub | 滚动条滑块 | `ScrollFill` | #303030 | `ScrollBack` | #171814 | 1.35 | 3.0 | #666666 | 3.11 |
| sub | 滚动条箭头 | `ScrollArrow` | #505050 | `ScrollBack` | #171814 | 2.21 | 3.0 | #646464 | 3.01 |
| sub | 缩进参考线 | `EdIndentVLine` | #484840 | `EdTextBg` | #272822 | 1.61 | 3.0 | #717168 | 3.02 |
| sub | 补全参数提示 | `ListCompleteParams` | #00A0A0 | `ListBg` | #404040 | 3.23 | 4.5 | #00BFBF | 4.54 |
| syn | 代码块括号连线 | `EdBlockStaple` | #B0B0B0 | `EdTextBg` | #FFFFFF | 2.17 | 3.0 | #949494 | 3.03 |
| syn | 十六进制视图 | `EdUnprintHexFont` | #A0A0A4 | `EdUnprintBg` | #E0E0E0 | 1.97 | 4.5 | #636367 | 4.53 |
| syn | 微缩图视口块 | `EdMicromapViewBg` | #808080 | `EdMicromapBg` | #E0E0E0 | 2.99 | 3.0 | #7D7D7D | 3.12 |
| syn | 折行标记符号 | `EdFoldMarkFont` | #8080E0 | `EdFoldMarkBg` | #FFFFFF | 3.45 | 4.5 | #6767DA | 4.64 |
| syn | 滚动条滑块 | `ScrollFill` | #CDCDCD | `ScrollBack` | #F0F0F0 | 1.39 | 3.0 | #888888 | 3.11 |
| syn | 禁用按钮（允许弱化） | `ButtonFontDisabled` | #888080 | `ButtonBgDisabled` | #D0C0C0 | 2.20 | 3.0 | #716A6A | 3.02 |
| syn | 缩进参考线 | `EdIndentVLine` | #A0A0A4 | `EdTextBg` | #FFFFFF | 2.61 | 3.0 | #949497 | 3.03 |
| syn | 补全参数提示 | `ListCompleteParams` | #808080 | `ListBg` | #F0F0F0 | 3.47 | 4.5 | #6C6C6C | 4.61 |
| syn | 选区文字 | `EdSelFont` | #E0E0E0 | `EdSelBg` | #0078D7 | 3.41 | 4.5 | #050505 | 4.53 |

## 弱化元素（仅记录，不建议修改）

| 主题 | 部位 | 实测 | 参考值 |
|---|---|---|---|
| amy | 不可打印字符（刻意弱化） | 2.25 | 3.0 |
| ebony | 不可打印字符（刻意弱化） | 1.62 | 3.0 |
| syn | 不可打印字符（刻意弱化） | 1.86 | 3.0 |

## 修正值落盘

全部建议值见 `tools/theme_wcag/theme_patches.json`。该脚本**不修改**任何主题文件；
应用方式：`python tools/theme_wcag/apply_patches.py syn sub`，只新增 `*_wcag` 主题副本。
