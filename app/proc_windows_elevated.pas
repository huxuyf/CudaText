(*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (c) Alexey Torgashin
*)
unit proc_windows_elevated;

{$mode ObjFPC}{$H+}

interface

function RunElevated(const AProgram, AParameters: UnicodeString; AHideWindow: boolean; ATimeout: DWORD): boolean;

implementation

uses
  Windows, ShellAPI, SysUtils, Classes, Forms;

function RunElevated(const AProgram, AParameters: UnicodeString; AHideWindow: boolean; ATimeout: DWORD): boolean;
var
  sei: TShellExecuteInfoW;
  nWait, nExit: DWORD;
begin
  Result := false;
  FillChar(sei, SizeOf(sei), 0);
  sei.cbSize := SizeOf(sei);
  sei.fMask := SEE_MASK_NOCLOSEPROCESS or SEE_MASK_UNICODE;
  sei.Wnd := Application.MainForm.Handle;
  sei.lpVerb := 'runas';
  sei.lpFile := PWideChar(AProgram);
  sei.lpParameters := PWideChar(AParameters);
  if AHideWindow then
    sei.nShow := SW_HIDE
  else
    sei.nShow := SW_SHOW;

  //ShellExecuteExW returns false if the user cancels the UAC prompt (ERROR_CANCELLED)
  if not ShellExecuteExW(@sei) then
    exit;

  try
    //do not kill the process on timeout: it may be still copying, and the caller's file check
    //can't be trusted anyway, so just report the operation as not confirmed
    nWait := WaitForSingleObject(sei.hProcess, ATimeout);
    if nWait <> WAIT_OBJECT_0 then
      exit(false);

    //success is only when the helper process finished with exit code 0
    if GetExitCodeProcess(sei.hProcess, nExit) then
      Result := (nExit = 0)
    else
      Result := true; //cannot query exit code, rely on the caller's result file check
  finally
    CloseHandle(sei.hProcess);
  end;
end;


end.

