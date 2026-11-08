(*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (c) Alexey Torgashin
*)
unit form_key_input;

{$mode objfpc}{$H+}

interface

uses
  Classes, SysUtils, Forms, Controls, Graphics,
  ButtonPanel, ExtCtrls, Menus, IniFiles,
  LCLProc, LCLType,
  ATSynEdit,
  proc_globdata,
  proc_customdialog,
  proc_msg;

type
  { TfmKeyInput }

  TfmKeyInput = class(TForm)
    ButtonPanel1: TButtonPanel;
    PanelPress: TPanel;
    procedure FormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
    procedure FormShow(Sender: TObject);
    procedure PanelPressMouseDown(Sender: TObject; Button: TMouseButton;
      Shift: TShiftState; X, Y: Integer);
  private
    { private declarations }
  public
    { public declarations }
    FHotkey: string;
  end;

function DoDialogHotkeyInput(ATitle: string): string;


implementation

{$R *.lfm}

function DoDialogHotkeyInput(ATitle: string): string;
var
  Form: TfmKeyInput;
begin
  Result:= '';
  Form:= TfmKeyInput.Create(nil);
  try
    if ATitle<>'' then
      Form.Caption:= ATitle;
    if Form.ShowModal=mrOk then
      Result:= Form.FHotkey;
  finally
    FreeAndNil(Form);
  end;
end;

{ TfmKeyInput }

procedure TfmKeyInput.FormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  if not AppKeyIsAllowedAsCustomHotkey(Key, Shift) then
  begin
    Key:= 0;
    exit
  end;

  if (Key=VK_ESCAPE) and (Shift=[]) then
  begin
    Key:= 0;
    ModalResult:= mrCancel;
    exit
  end;

  FHotkey:= ShortCutToTextRaw(ShortCut(Key, Shift));
  ModalResult:= mrOk;
  Key:= 0;
end;

procedure TfmKeyInput.FormShow(Sender: TObject);
begin
  ButtonPanel1.OKButton.Caption:= '确定';
  ButtonPanel1.CancelButton.Caption:= '取消';

  DoForm_ScaleAuto(Self);
  UpdateFormOnTop(Self);
end;

procedure TfmKeyInput.PanelPressMouseDown(Sender: TObject;
  Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
begin
  if HandleMouseDownToHandleExtraMouseButtons(Self, Button, Shift) then exit;
end;

end.