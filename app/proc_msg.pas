(*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (c) Alexey Torgashin
*)
unit proc_msg;

{$mode objfpc}{$H+}

interface

uses
  SysUtils,
  ATBinHex;

const
  cAppExeVersion = '1.239.0.1';
  cAppApiVersion = '1.0.486';

const
  cOptionSystemSuffix =
    {$ifdef windows} '' {$endif}
    {$ifdef linux} '__linux' {$endif}
    {$ifdef darwin} '__mac' {$endif}
    {$ifdef freebsd} '__freebsd' {$endif}
    {$ifdef netbsd} '__netbsd' {$endif}
    {$ifdef openbsd} '__openbsd' {$endif}
    {$ifdef dragonfly} '__dragonfly' {$endif}
    {$ifdef solaris} '__solaris' {$endif}
    {$ifdef haiku} '__haiku' {$endif}
    ;

  cSystemLibDir =
    {$ifdef windows} '' {$endif}
    {$ifdef linux} '/usr/lib' {$endif}
    {$ifdef darwin} '/Library/Frameworks' {$endif}
    {$ifdef freebsd} '/usr/local/lib' {$endif}
    {$ifdef netbsd} '/usr/pkg/lib' {$endif}
    {$ifdef openbsd} '/usr/local/lib' {$endif}
    {$ifdef dragonfly} '/usr/lib' {$endif}
    {$ifdef solaris} '/usr/lib/amd64' {$endif}
    {$ifdef haiku} '/system/lib' {$endif}
    ;

  cSystemHasPkExec =
    {$ifdef windows}   false {$endif}
    {$ifdef linux}     true {$endif}
    {$ifdef darwin}    false {$endif}
    {$ifdef freebsd}   true {$endif}
    {$ifdef netbsd}    true {$endif}
    {$ifdef openbsd}   true {$endif}
    {$ifdef dragonfly} true {$endif}
    {$ifdef solaris}   true {$endif}
    {$ifdef haiku}     false {$endif}
    ;

  cCannotSaveToWriteProtectedDirButDontWantPkExec =
    {$ifdef windows}   false {$endif}
    {$ifdef linux}     false {$endif}
    {$ifdef darwin}    false {$endif}
    {$ifdef freebsd}   true {$endif}
    {$ifdef netbsd}    true {$endif}
    {$ifdef openbsd}   true {$endif}
    {$ifdef dragonfly} true {$endif}
    {$ifdef solaris}   true {$endif}
    {$ifdef haiku}     false {$endif}
    ;

const
  EOL = #10;
  msgPythonListError = 'Cannot create new list object'; //no need i18n
  msgCallbackBad = 'NOTE: Bad API callback, report to plugin author: %s'; //no i18n
  msgApiDeprecated = 'NOTE: Deprecated API usage: %s'; //no i18n
  msgErrorInTheme = '注意：主题 “%s” 缺少条目 “%s”';
  msgRescannedAllPlugins = '已重新扫描所有插件';
  msgWelcomeTabTitle = '欢迎';
  msgSavedPythonLibOption = '已保存选项 "pylib'+cOptionSystemSuffix+'"。重启 CudaText 后生效。';
  msgSearchingInDir = '正在搜索：';
  msgErrorLowDiskSpaceMb = '磁盘可用空间小于 %d Mb。请释放一些空间，然后点击“重试”。';
  msgErrorNullBytesInFile = '配置文件已损坏，因为其前导字节为 NULL：'#10'%s'#10'按“确定”删除它。';

  msgCmdPaletteCaption: string = '命令面板';
  msgCmdPaletteTextHint: string = '按 F9 设置热键，按 @ 查找热键，按 # 求助';
  msgCmdPalettePrefixHelp: string = '#p – 插件'+EOL+'#l – 词法分析器'+EOL+'#f – 已打开的文件'+EOL+'#r – 最近的文件'+EOL+'@name – 在当前文件中转到符号'+EOL+':N – 转到第 N 行';
  msgCmdPaletteGotoLine: string = '转到第 %s 行 — 按 Enter';
  msgCmdPaletteNoSymbols: string = '当前文件未找到符号（此词法分析器没有代码树辅助程序）。';
  msgCmdPaletteNoMatch: string = '没有匹配的符号。';

  msgErrorPluginIgnored = '注意：插件 %s 在忽略列表中，请将其移除';
  msgErrorTooManyFileTabs = '注意：打开的编辑器标签过多，无法添加新标签';
  msgCannotFindLexers = '注意：找不到词法分析器：%s';
  msgCannotFindData = '错误：找不到数据：%s';
  msgCannotFindSessionFile = '注意：会话中的文件未找到：%s';
  msgBadLexerName = '错误："newdoc_lexer" 中的词法分析器名称不正确："%s"';

  msgTitle = 'CudaText'; //no i18n
  msgModifiedString: array[boolean] of string = ('', '*'); //no i18n
  msgLiteLexerSuffix = ' ^'; //no i18n
  msgStatusbarCellMouseColumnSel: string = '鼠标列';
  msgStatusbarCellKeybdColumnSel: string = '键盘列';
  msgStatusbarCellInsOvr: array[boolean] of string = ('插入', '覆盖');
  msgStatusbarCellReadOnly: string = '只读';

  msgDialogTitleOpen: string = '打开文件';
  msgDialogTitleSaveAs: string = '文件另存为';

  msgFileMaybeNotText: string = 'File is maybe not text:';
  msgFileTooBig: string = 'File is too big to edit:';
  msgDetectedBinaryChar: string = 'Detected binary char:';

  msgTooltipCloseTab: string = '关闭标签页';
  msgTooltipAddTab: string = '添加标签页';
  msgTooltipArrowLeft: string = '向左滚动标签栏';
  msgTooltipArrowRight: string = '向右滚动标签栏';
  msgTooltipArrowMenu: string = '显示标签菜单';

  msgUntitledEnglish = 'Untitled';
  msgUntitledTab: string = '无标题';
  msgAllFiles: string = '所有文件';
  msgNoLexer: string = '（无词法分析器）';
  msgIgnoredCommandIfNotFocused: string = '忽略该命令：编辑器当前未获得焦点';
  msgOpenLink: string = '打开 %s';

  msgPanelMenu_Init = 'Menu';
  msgPanelTree_Init = 'Code-Tree';
  msgPanelProject_Init = 'Project';
  msgPanelTabs_Init = 'Tabs';
  msgPanelSnippet_Init = 'Snippet Panel';

  msgPanelConsole_Init = 'Console';
  msgPanelOutput_Init = 'Output';
  msgPanelValidate_Init = 'Validate';
  msgPanelSearch_Init = 'Search';

  msgPanelMenu: string = '菜单';
  msgPanelTree: string = '代码树';
  msgPanelProject: string = '项目';
  msgPanelTabs: string = '标签列表';
  msgPanelSnippet: string = '片段面板';

  msgPanelConsole: string = '控制台';
  msgPanelOutput: string = '输出';
  msgPanelValidate: string = '验证';
  msgPanelSearch: string = '搜索';

  msgFinderHintRegex: string = '正则表达式';
  msgFinderHintCase: string = '区分大小写';
  msgFinderHintWords: string = '单词';
  msgFinderHintBack: string = '后退';
  msgFinderHintWrapped: string = '换行';
  msgFinderHintInSel: string = '在选区中';
  msgFinderHintFromCaret: string = '从插入点';
  msgFinderHintSearchWrapped: string = '横向边';
  msgFinderHintPresCase: string = '保留大小写';
  msgFinderRegexMathes: string = '正则匹配数';

  msgButtonOk: string = '确定';
  msgButtonCancel: string = '取消';
  msgButtonApply: string = '应用';
  msgButtonClose: string = '关闭';
  msgButtonYes: string = '是(&Y)';
  msgButtonNo: string = '否(&N)';
  msgButtonYesAll: string = '全是(&A)';
  msgButtonNoAll: string = '全否';
  msgButtonAbort: string = '中止';
  msgButtonRetry: string = '重试';
  msgButtonIgnore: string = '忽略';

  msgFileNew: string = '新建文件';
  msgFileOpen: string = '打开文件...';
  msgFileSave: string = '保存';
  msgFileRename: string = '重命名...';
  msgFileClearList: string = '清除列表';
  msgCopySub: string = '复制到剪贴板';
  msgCopyFilenameName: string = '仅复制文件名';
  msgCopyFilenameDir: string = '仅复制文件路径';
  msgCopyFilenameFull: string = '复制完整文件路径';
  msgCopyCurrentLine: string = '复制当前行';

  msgEndWin = 'CRLF';
  msgEndUnix = 'LF';
  msgEndMac = 'CR';

  msgPythonFindCaption: string = '查找 Python 库';
  msgPythonFindCaptionLong = '未找到 Python 引擎；请手动查找...';
  msgPythonFindFromDir: string = '在此文件夹及其所有子文件夹中搜索 Python 库：';
  msgCannotFindPython: string = '找不到 Python 库';

  msgCannotInitPythonDisabled: string = '注意：Python 引擎已被禁用';
  msgCannotInitPython1: string = '注意：未找到 Python 3 引擎。Python 插件当前不可用。要解决此问题：';
  {$ifdef darwin}
  msgCannotInitPython2: string = '请从 www.python.org 安装 Python 3.x，之后 CudaText 应能自动找到它。';
  msgCannotInitPython2b: string = '';
  {$else}
    {$ifdef windows}
    msgCannotInitPython2: string = '请将以下文件放到 cudatext.exe 旁边：python3x.dll、python3x.zip、python3xdlls\*.pyd、MS VS Runtime。';
    msgCannotInitPython2b: string = '';
    {$else}
    msgCannotInitPython2: string = '* 在 user.json 中写入 "pylib'+cOptionSystemSuffix+
                                   '"；关于 "pylib" 的说明见 "选项 / 默认设置"。';
    msgCannotInitPython2b: string = '* 或使用菜单项 "插件 / '+msgPythonFindCaptionLong+'"';
    {$endif}
  {$endif}

  msgCannotOpenFile: string = '无法打开文件：';
  msgCannotFindFile: string = '找不到文件：';
  msgCannotFindFolder: string = '找不到文件夹：';
  msgCannotOpenNoReadPermissions: string = '没有读取权限。';
  msgCannotHandleSplittedTab: string = '无法处理拆分后的 UI 标签页';
  msgCannotHandleUntitledTab: string = '无法处理未命名文档';
  msgCannotFindLexerInLibrary: string = '在库中找不到词法分析器：';
  msgCannotFindLexerFile: string = '找不到词法分析器文件：';
  msgCannotLoadLexerFile: string = '无法加载词法分析器：';
  msgCannotFindSublexerInLibrary: string = '在库中找不到链接的子词法分析器：';
  msgCannotFindWithoutCaret: string = '没有光标时无法查找/替换';
  msgCannotCreateDir: string = '无法创建目录：';
  msgCannotSaveFile: string = '无法保存文件：';
  msgCannotSaveFileTempRemoved: string = '临时副本已被删除；文本仍保留在编辑器中。';
  msgCannotSaveFileWithEnc: string = '无法保存文件，因为编码 "%s" 无法处理 Unicode 文本。程序已将文件保存为 UTF-8 编码。';
  msgCannotSaveUserConf: string = '无法保存用户配置（只读？）';
  msgCannotLoadFileInUTF8: string = '无法以 UTF-8 加载文件，UTF-8 序列不正确';
  msgCannotReadConfig: string = '无法读取/解析配置：';
  msgCannotReloadUntitledTab: string = '无法重新打开无标题标签';
  msgCannotFindInMultiSel: string = 'Cannot find in multi-selections, yet';
  msgCannotFindMatch: string = '找不到';
  msgCannotFindInstallInfInZip: string = '在 zip 文件的根目录中找不到 install.inf';
  msgCannotFindBookmarks: string = '在文本中找不到标记';
  msgCannotHandleZip: string = '无法处理 zip 文件：';
  msgCannotSetHotkey: string = '无法为此项设置快捷键';
  msgCannotInstallAddonApi: string = '无法安装加载项 "%s"，它需要较新的应用程序版本（API %s）';
  msgCannotInstallOnOS: string = '无法安装附加组件 "%s"：它需要其他操作系统（%s）';
  msgCannotInstallReqPlugin: string = '无法安装 "%s"：缺少所需插件（%s）';
  msgCannotInstallReqLexer: string = '无法安装 "%s"：缺少所需词法分析器（%s）';
  msgCannotAutocompleteMultiCarets: string = '自动完成不适用于多个插入点';
  msgCannotSetWrap: string = '无法设置自动换行模式。行数 %d 大于选项“wrap_enabled_max_lines”的值：%d。';
  msgCannotSaveAndDontWantToRunPkExec = '无法保存到受写保护的文件夹。请以 root 身份运行：';

  msgStatusbarTextTab: string = '制表符';
  msgStatusbarTextSpaces: string = '空格';

  msgStatusbarTextLine: string = '行';
  msgStatusbarTextCol: string = '列';
  msgStatusbarTextSel: string = '选择';
  msgStatusbarTextLinesSel: string = '选择行';
  msgStatusbarTextCarets: string = '插入点';

  msgStatusbarFoundInVisibleArea: string = '（可见区域）';

  {
  //this is not used anymore, statusbar panel 'wrap' shows graphics now
  msgStatusbarWrapStates: array[0..Ord(High(TATEditorWrapMode))] of string =
    ('→', '↵', '↵│');
    }

  msgStatusbarHintCaret: string = '光标位置，选择';
  msgStatusbarHintEnc: string = '文件编码';
  msgStatusbarHintLexer: string = '词法分析器（语言）';
  msgStatusbarHintEnds: string = '行尾字符';
  msgStatusbarHintSelMode: string = '无需 Alt 键即可使用鼠标/键盘选择列';
  msgStatusbarHintTabSize: string = '制表符宽度，以空格字符为单位';
  msgStatusbarHintInsOvr: string = '插入/覆盖模式';
  msgStatusbarHintWrap: string = '自动换行（关闭，按窗口，按边距）';
  msgStatusbarHintZoom: string = '缩放值';
  msgStatusbarHintReadOnly: string = '只读模式';

  msgStatusSaveIsIgnored: string = '已忽略“保存”命令（文件尚未修改）';
  msgStatusPluginHotkeyBusy: string = '警告：快捷键 [%s] 已被占用，未设置成功';
  msgStatusSyntaxThemesOff: string = '语法主题已通过选项 "ui_lexer_themes": false 关闭。因此以下对话框将无效。若要自定义样式，请使用“词法分析器属性”对话框。';
  msgStatusIncorrectInstallInfInZip: string = 'zip 包中的 install.inf 文件不正确';
  msgStatusUnsupportedAddonType: string = '不支持的插件类型：';
  msgStatusPackageContains: string = '此安装包包含：';
  msgStatusPackageName: string = '名称：';
  msgStatusPackageType: string = '类型：';
  msgStatusPackageDesc: string = '描述：';
  msgStatusPackageCommand: string = '命令：';
  msgStatusPackageEvents: string = '事件：';
  msgStatusPackageLexer: string = '词法分析器：';
  msgStatusPackageLexerSettings: string = '词法分析器设置：';
  msgStatusPackageAutoCompletion: string = '静态自动补全：';
  msgStatusPackageData: string = '数据：';
  msgStatusPackageFormatter: string = '格式化程序：';
  msgStatusPackageLinter: string = '代码检查工具：';
  msgStatusPackagePackage: string = '包：';
  msgStatusPackageMissedLexerMap: string = '词法分析器缺少主题支持（.cuda-lexmap 文件）';
  msgStatusInstalledNeedRestart: string = '插件将在程序重启后生效';
  msgStatusCommandOnlyForLexers: string = '此命令仅适用于词法分析器：';
  msgStatusOpenedBrowser: string = '已打开浏览器';
  msgStatusCopiedLink: string = '已复制链接';
  msgStatusAddonInstalled: string = '插件已安装';
  msgStatusAddonsInstalled: string = '已安装多个插件（最多 %d 个）';
  msgStatusOpened: string = '已打开：';
  msgStatusClosed: string = '已关闭：';
  msgStatusReopened: string = '已重新打开：';
  msgStatusSavedFile: string = '已保存：';
  msgStatusBadRegex: string = '传入的正则表达式不正确：';
  msgStatusFoundNextMatch: string = '找到下一个匹配项';
  msgStatusTryingAutocomplete: string = '正在尝试自动补全：';
  msgStatusReplaceCount: string = '已替换：%d 处';
  msgStatusFoundFragments: string = '找到 %d 个片段';
  msgStatusReadingOps: string = '正在读取选项';
  msgStatusPictureNxN: string = '图像 %dx%d';
  msgStatusCancelled: string = '已取消';
  msgStatusBadLineNum: string = '输入的行号不正确';
  msgStatusEndsChanged: string = '行尾符已更改';
  msgStatusEncChanged: string = '编码已更改';
  msgStatusGotoFileLineCol: string = '文件“%s”，第 %d 行，第 %d 列';
  msgStatusClickingLogLine: string = '正在点击日志行';
  msgStatusNoGotoDefinitionPlugins: string = '此词法分析器未安装“跳转到定义”插件';
  msgStatusFilenameAlreadyOpened: string = '文件名已在另一个选项卡中打开：';
  msgStatusNeedToCloseTabSavedOrDup: string = '您需要关闭选项卡：另存为或重复的选项卡。';
  msgStatusHotkeyBusy: string = '快捷键已被占用：%s';
  msgStatusChangedLinesCount: string = '已更改 %d 行';
  msgStatusFontSizeChanged: string = '字体大小已更改为 %d%%';
  msgStatusLexerDisabledBySize: string = '选项 "ui_max_size_lexer":%d 已在此文件中禁用词法分析器“%s”（文件大小：%d Mb）';
  msgStatusDetectedBinaryChar: string = '检测到二进制字符 0x%s，位于文件 “%s”';
  msgStatusUndoStopped: string = '撤销功能已在第 %s 行停止，请参见选项 "max_line_len_for_undo": %d（点击隐藏）';

  msgConfirmHotkeyBusy: string = '快捷键已被以下命令占用：'#10'%s'#10''#10'是否覆盖？';
  msgConfirmHotkeyList: string = '快捷键 (%d)：%s';
  msgConfirmOkNoHotkeys: string = '确定（不使用快捷键）';
  msgConfirmSyntaxThemeSameName: string = '语法主题已存在，且与界面主题同名。是否也应用该语法主题？';
  msgConfirmInstallIt: string = '是否要安装它？';
  msgConfirmFileChangedOutside: string = '文件在外部被修改：';
  msgConfirmFileDeletedOutside: string = '文件在外部被删除：';
  msgConfirmReloadIt: string = '是否重新打开？';
  msgConfirmReloadYes: string = '重新打开';
  msgConfirmReloadYesAlways: string = '自动重新打开此文件';
  msgConfirmReloadNoMore: string = '不再询问此文件';
  msgConfirmReloadItHotkeysSess: string = '(是：重新打开。否：加载上一会话的文本。)';
  msgConfirmOpenCreatedDoc: string = '是否打开已创建的文档？';
  msgConfirmSaveColorsToFile: string = '是否将主题保存到文件？';
  msgConfirmSaveModifiedTab: string = '在关闭前是否将更改保存到文档“%s”？'#10''#10'如果不保存，更改将永久丢失。';
  msgConfirmClosePinnedTab: string = '文档已被固定：'#10'%s'#10''#10'确定要关闭它吗？';
  msgConfirmReopenModifiedTab: string = '文档已被修改：'#10'%s'#10''#10'是否重新打开？';
  msgConfirmReloadFileWithEnc: string = '内存中的编码已更改。'#10'是否还要重新打开文件？';
  msgConfirmCreateNewFile: string = '未找到文件：'#10'%s'#10''#10'是否创建它？';
  msgConfirmCreateUserConfig: string = '未找到用户配置。是否创建？';
  msgConfirmCloseAndDeleteFile: string = '是否关闭选项卡并删除其文件？';
  msgConfirmDeleteLexer: string = '是否删除词法分析器“%s”？';
  msgConfirmRemoveStylesFromBackup: string = '是否从备份文件中移除已勾选的样式？';
  msgConfirmReplaceGlobal: string = '这将在所有打开的文档中执行批量替换。此操作还会重置所有选择。是否继续？';

  msgCommandNeedsPython: string =
    '此命令需要 Python 引擎。'
    {$ifndef windows}
    +' 请在 user.json 中正确设置 "pylib'+cOptionSystemSuffix+'"。'
    {$endif}
    ;

  msgCommandLineHelp =
      'Usage:'+EOL+
      '  cudatext [ key ... ] filename ...'+EOL+
      ''+EOL+
      'Supported keys:'+EOL+
      '  -h, --help      - Show this help and exit'+EOL+
      '  -v, --version   - Show application version and exit'+EOL+
      '  -z=[text|binary|hex|unicode|uhex] - Open arguments in internal viewer'+EOL+
      '  -r              - Open arguments in read-only mode'+EOL+
      '  -e=value        - Open arguments in given encoding'+EOL+
      '  -el             - Show supported encoding names, exit'+EOL+
      '  -n              - Ignore option "ui_one_instance", open new app window'+EOL+
      '  -nh             - Ignore saved file history'+EOL+
      '  -nsl            - No session loading on start'+EOL+
      '  -nss            - No session saving on exit'+EOL+
      '  -ns             - The same as -nsl and -nss'+EOL+
      '  -nn             - Don''t suggest to create new file if filename not found'+EOL+
      '  -s=folder       - Set full path of "settings" folder'+EOL+
      '  -i              - Open contents of stdin in new tab (Unix only)'+EOL+
      '  -verbose        - Copy Python messages to stdout (Unix only)'+EOL+
      '  -id=name - Set single-instance id, for groups of instances (Unix, default: cudatext.0)'+EOL+
      '  -w=left,top,width,height        - Set position/size of the main window'+EOL+
      '  -c=cuda_module,method           - Run command plugin on startup'+EOL+
      '  -p=cuda_module#param1#param2... - Run event "on_cli" on startup'+EOL+
      ''+EOL+
      'Filenames can be with "@line" or "@line@column" suffix to place caret.'+EOL+
      'Folder can be passed, will be opened in Project Manager plugin.'+EOL+
      'Projects (*.cuda-proj) can be passed, will be opened in Project Manager.'+EOL;
      //'Sessions (*.cuda-session) can be passed, even without Session Manager plugin.'+EOL;

  msgFirstStartInfo =
      '            ____          _      _____         _   '+EOL+
      '           / ___|   _  __| | __ |_   _|____  _| |_ '+EOL+
      '          | |  | | | |/ _` |/ _` || |/ _ \ \/ / __|'+EOL+
      '          | |__| |_| | (_| | (_| || |  __/>  <| |_ '+EOL+
      '           \____\__,_|\__,_|\__,_||_|\___/_/\_\\__|'+EOL+
      '---------------------------------------------------------------'+EOL+
      '这是 CudaText 的首次启动（未找到文件 history.json）。'+EOL+
      '如果已配置 Python 引擎，你可以安装常用附加组件'+EOL+
      '使用菜单项 "插件 / 多重安装器"。'+EOL+
      '---------------------------------------------------------------'+EOL+
      '你可以双击此视频教程链接：'+EOL+
      'https://www.youtube.com/watch?v=q8edzSd400Y'+EOL+
      '---------------------------------------------------------------'+EOL;

const
  msgViewer: string = '查看器';
  msgViewerModes: array[TATBinHexMode] of string = (
    '纯文本',
    '二进制',
    '十六进制',
    'unicode 文本',
    'unicode 文本/十六进制混合模式'
    );

  msgTextCaseMenu: string = '转换大小写';
  msgTextCaseUpper: string = '大写';
  msgTextCaseLower: string = '小写';
  msgTextCaseTitle: string = '字首大写';
  msgTextCaseInvert: string = '反转大小写';
  msgTextCaseSentence: string = '句首大写';

  msgFindHint_InputFind: string = 'Find what';
  msgFindHint_InputRep: string = 'Replace with';
  msgFindHint_FindFirst: string = 'Find first';
  msgFindHint_FindNext: string = 'Find next';
  msgFindHint_FindPrev: string = 'Find previous';
  msgFindHint_Rep: string = 'Replace next match';
  msgFindHint_RepAll: string = 'Replace all matches in current document';
  msgFindHint_RepGlobal: string = 'Replace all matches in all opened tabs';
  msgFindHint_Regex: string = 'Regular expressions';
  msgFindHint_RegexSubst: string = 'RegEx substitution for ''Replace with''';
  msgFindHint_Case: string = 'Case sensitive';
  msgFindHint_Words: string = 'Whole words';
  msgFindHint_Wrapped: string = 'Wrapped search';
  msgFindHint_ConfirmRep: string = 'Confirm on replace';
  msgFindHint_MultiLine: string = 'Multi-line input (Ctrl+Enter for new-line)';
  msgFindHint_InSelect: string = 'Search in selection';
  msgFindHint_Tokens: string = 'Allowed syntax elements';
  msgFindHint_HiAll: string = 'Highlight all matches';
  msgFindHint_Immediate: string = 'Immediate search (find as you type)';
  msgFindHint_PresCase: string = 'Preserve case on replacement';

function msgPanelCaption(const ACaption: string): string;
function msgFinderRegexMatchesNumbered: string;
function IsUntitledEnglishTabCaption(const ACaption: string): boolean;

implementation

uses
  ATStringProc;

function msgPanelCaption(const ACaption: string): string;
begin
  case ACaption of
    msgPanelTree_Init:
      Result:= msgPanelTree;
    msgPanelProject_Init:
      Result:= msgPanelProject;
    msgPanelTabs_Init:
      Result:= msgPanelTabs;
    msgPanelSnippet_Init:
      Result:= msgPanelSnippet;
    msgPanelConsole_Init:
      Result:= msgPanelConsole;
    msgPanelOutput_Init:
      Result:= msgPanelOutput;
    msgPanelValidate_Init:
      Result:= msgPanelValidate;
    else
      Result:= ACaption;
  end;
end;

function msgFinderRegexMatchesNumbered: string;
const
  NCounter: integer = 0;
begin
  Inc(NCounter);
  Result:= msgFinderRegexMathes+' '+IntToStr(NCounter);
end;

function IsUntitledEnglishTabCaption(const ACaption: string): boolean;
var
  i: integer;
begin
  Result:= SBeginsWith(ACaption, msgUntitledEnglish) and
    (Length(ACaption)>Length(msgUntitledEnglish));
  if Result then
    for i:= Length(msgUntitledEnglish)+1 to Length(ACaption) do
      if not IsCharDigit(ACaption[i]) then
        exit(false);
end;


end.
