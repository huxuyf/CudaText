(*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (c) Alexey Torgashin
*)
unit proc_editor_saving;

{$mode objfpc}{$H+}

interface

uses
  ATSynEdit;

function EditorSaveFileAs(Ed: TATSynEdit; const AFileName: string): boolean;


implementation

uses
  SysUtils, StrUtils,
  Classes, Controls, LCLType,
  FileUtil, LazFileUtils,
  {$ifdef windows}
  proc_windows_elevated,
  {$else}
  Process,
  {$endif}
  proc_files,
  proc_msg,
  proc_globdata;

const
  BadWindowsChars = ':*?\|<>"';

function SReplaceBadChars(const S: string): string;
var
  i: SizeInt;
begin
  Result:= S;
  for i:= 1 to Length(Result) do
    if Pos(Result[i], BadWindowsChars)>0 then
      Result[i]:= '_';
end;


procedure SaveSimple(Ed: TATSynEdit; const fn: string);
var
  dir, fn_name, fn_changed, fn_old_bad: string;
begin
  dir:= ExtractFileDir(fn);
  if not DirectoryExists(dir) then
  begin
    if ForceDirectory(dir) then
      MsgLogConsole('注意：保存时文件的文件夹不存在，已重新创建：'+dir)
    else
      MsgLogConsole('错误：保存时文件的文件夹不存在，且无法重新创建：'+dir);

    if not DirectoryExists(dir) then
    begin
      MsgBox(
        msgCannotSaveFile+#10+AppCollapseHomeDirInFilename(fn)+#10#10+
        msgCannotFindFolder+#10+AppCollapseHomeDirInFilename(dir),
        MB_OK or MB_ICONERROR);
      exit;
    end;
  end;

  try
    Ed.SaveToFile(fn);
  except
    //if user saves filename '/path/aa:bb:cc' on Linux on exFAT disk, try to replace ':' chars
    fn_name:= ExtractFileName(fn);
    if PosSet(BadWindowsChars, fn_name)>0 then
    begin
      fn_old_bad:= fn_name;
      fn_name:= SReplaceBadChars(fn_name);
      fn_changed:= dir+DirectorySeparator+fn_name;
      Ed.SaveToFile(fn_changed);
      Ed.FileName:= fn_changed;
      MsgLogConsole('注意：文件名中的非法字符 '+BadWindowsChars+'；文件名已改为 "'+fn_changed+'"，原为 "'+fn_old_bad+'"');
    end
    else
      raise;
  end;
end;

function IsBadResultFile(const fn: string; AllowEmpty: boolean): boolean;
begin
  Result:= (not FileExists(fn)) or
    (not AllowEmpty and (FileUtil.FileSize(fn)=0));
end;

//timeout for the elevated copy helper: base time + time per KB of the copied file, with a cap
function TimeoutForElevatedCopy(const fn: string): DWORD;
const
  cBaseMs = 6000;
  cPerKbMs = 20;
  cMaxExtraMs = 174000;
var
  nSize, nExtra: Int64;
begin
  nSize:= FileSizeUtf8(fn);
  if nSize<0 then
    nSize:= 0;
  nExtra:= (nSize div 1024) * cPerKbMs;
  if nExtra>cMaxExtraMs then
    nExtra:= cMaxExtraMs;
  Result:= DWORD(cBaseMs + nExtra);
end;

procedure MsgBox_CannotSaveFile(const fn: string);
begin
  MsgBox(msgCannotSaveFile+#10+AppCollapseHomeDirInFilename(fn)+#10#10+
         msgCannotSaveFileTempRemoved,
         MB_OK or MB_ICONERROR);
end;

//save the editor text to a temp file in the target's folder, then replace the
//target atomically, so a crash or a power loss cannot destroy the original file.
//returns true when the save is complete (also when an error was reported),
//and false when the legacy save path must be used instead
function SaveAtomic(Ed: TATSynEdit; const fn: string): boolean;
var
  fnTemp: string;
  bDocEmpty: boolean;
  bOK: boolean;
  dir: string;
begin
  Result:= false;

  dir:= ExtractFileDir(fn);
  //missing folder: let SaveSimple either re-create it or show its error
  if not DirectoryExists(dir) then exit;

  //don't replace a symlink, the link itself must stay; use the legacy path
  if AppFileIsSymlink(fn) then exit;

  fnTemp:= AppTempFileNameInDir(dir, '.cudatext-');
  if fnTemp='' then exit;

  bDocEmpty:= Ed.IsEmpty;
  bOK:= false;
  try
    try
      SaveSimple(Ed, fnTemp);
      bOK:= true;
    finally
      //Ed.SaveToFile changes the editor filename
      Ed.FileName:= fn;
    end;
  except
    on E: EConvertError do
    begin
      //let the caller retry with UTF-8 encoding
      AppFileDeleteForced(fnTemp);
      raise;
    end;
    on E: Exception do
      bOK:= false;
  end;

  if not bOK then
  begin
    //if the temp file was created, the failure can be "no disk space"; then don't
    //retry by writing the target directly, because it would truncate the original
    if FileExists(fnTemp) then
    begin
      AppFileDeleteForced(fnTemp);
      MsgBox_CannotSaveFile(fn);
      exit(true); //error is reported, the original file is intact
    end;
    //no temp file at all: write-protected folder or bad path, let the legacy path
    //re-create the folder or use the elevated copy
    exit(false);
  end;

  if IsBadResultFile(fnTemp, bDocEmpty) then
  begin
    AppFileDeleteForced(fnTemp);
    MsgBox_CannotSaveFile(fn);
    exit(true);
  end;

  //flush the data and close the file, only then the temp file may replace the target
  AppFileFlushToDisk(fnTemp);

  //keep attributes, permissions, owner and creation time of the original file
  AppFileCopyMetadata(fn, fnTemp);

  if AppFileReplaceAtomic(fnTemp, fn) then
    exit(true);

  //the replacement failed (e.g. the target is locked by another program), the
  //original is still intact: remove the temp and use the legacy path
  AppFileDeleteForced(fnTemp);
  Result:= false;
end;

procedure SaveViaTempCopy(Ed: TATSynEdit; const fn: string);
var
  fnTemp: string;
  //
  procedure MsgBox_ErrorTempRemoved;
  begin
    //do not keep the temp file on failure, so the message must not point to it
    DeleteFile(fnTemp);
    MsgBox_CannotSaveFile(fn);
  end;
  //
var
  bDocEmpty: boolean;
  {$ifdef windows}
  SCopyParams: UnicodeString;
  {$else}
  SOutput: string;
  {$endif}
  dir: string;
begin
  dir:= ExtractFileDir(fn);
  if not DirectoryExists(dir) then
  begin
    MsgBox(msgCannotSaveFile+#10+AppCollapseHomeDirInFilename(fn)+#10#10+
           msgCannotFindFolder+#10+AppCollapseHomeDirInFilename(dir),
           MB_OK or MB_ICONERROR);
    exit;
  end;

  bDocEmpty:= Ed.IsEmpty;
  fnTemp:= GetTempFileName('', 'cudatext_');
  SaveSimple(Ed, fnTemp);
  Ed.FileName:= fn; //Ed.FileName was changed to fnTemp

  if IsBadResultFile(fnTemp, bDocEmpty) then
  begin
    MsgBox_ErrorTempRemoved;
    exit;
  end;

  {$ifdef windows}
  SCopyParams:= UnicodeFormat('/C echo F | xcopy "%s" "%s" /r /h /y', [fnTemp, fn]);
  if not RunElevated('cmd.exe', SCopyParams, true, TimeoutForElevatedCopy(fnTemp)) then
  begin
    MsgBox_ErrorTempRemoved;
    exit;
  end;
  {$else}
  if cSystemHasPkExec and UiOps.AllowRunPkExec then
  begin
    if FileIsWritable(fn) then
    begin
      if not CopyFile(fnTemp, fn) then
      begin
        MsgBox_ErrorTempRemoved;
        exit;
      end;
    end
    else
    if cCannotSaveToWriteProtectedDirButDontWantPkExec then
      //this message shows the manual copy command with fnTemp, so the temp file must be kept
      MsgBox(msgCannotSaveAndDontWantToRunPkExec+#10#10+
             Format('cp -T "%s" "%s"', [fnTemp, fn]), MB_OK or MB_ICONWARNING)
    else
    if not RunCommand('pkexec', ['/bin/cp', '-T', fnTemp, fn], SOutput, [poWaitOnExit]) then
    begin
      MsgBox_ErrorTempRemoved;
      exit;
    end;
  end
  else
  if not CopyFile(fnTemp, fn) then
  begin
    MsgBox_ErrorTempRemoved;
    exit;
  end;
  {$endif}

  if IsBadResultFile(fn, bDocEmpty) then
  begin
    MsgBox_ErrorTempRemoved;
    exit;
  end;

  DeleteFile(fnTemp);
end;


function EditorSaveFileAs(Ed: TATSynEdit; const AFileName: string): boolean;
var
  OldEncoding: string;
  OldAttr: Longint;

  procedure SaveLegacy;
  begin
    try
      SaveSimple(Ed, AFileName);
    except
      on E: EFOpenError do
        SaveViaTempCopy(Ed, AFileName);
      on E: EWriteError do //on Linux, saving to smb folder fails, issue #3435
        SaveViaTempCopy(Ed, AFileName);
    end;
  end;

begin
  Result:= true;
  while true do //loop attempts forever, until correct saving which calls Break
    try
      AppFileAttrPrepare(AFileName, OldAttr);

      try
        //main path: temp file in the target folder + atomic replacement
        if not SaveAtomic(Ed, AFileName) then
          SaveLegacy;
      except
        on E: EConvertError do
          begin
            OldEncoding:= Ed.EncodingName;
            Ed.EncodingName:= cEncNameUtf8_NoBom;
            if not SaveAtomic(Ed, AFileName) then
              SaveLegacy;
            MsgBox(Format(msgCannotSaveFileWithEnc, [OldEncoding]), MB_OK or MB_ICONWARNING);
          end;
        else
          raise;
      end;

      Ed.Update; //'line states' maybe changed by saving
      AppFileAttrRestore(AFileName, OldAttr);
      Break; //break the 'while true do'
    except
      on E: Exception do
      begin
        if MsgBox(E.ClassName+#10+E.Message, MB_RETRYCANCEL or MB_ICONERROR) = IDCANCEL then
          exit(false);
      end;
    end;
end;

end.

