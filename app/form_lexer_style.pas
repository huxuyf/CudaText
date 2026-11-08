(*
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (c) Alexey Torgashin
*)
unit form_lexer_style;

{$mode objfpc}{$H+}

interface

uses
  Classes, SysUtils, FileUtil, Forms, Controls, Graphics, Dialogs, ExtCtrls,
  ColorBox, StdCtrls, ButtonPanel, IniFiles,
  ec_SyntAnal,
  ec_syntax_format,
  proc_colors,
  proc_globdata,
  proc_msg;

type
  { TfmLexerStyle }

  TfmLexerStyle = class(TForm)
    ButtonPanel1: TButtonPanel;
    cbBorderB: TComboBox;
    cbBorderL: TComboBox;
    cbBorderR: TComboBox;
    cbBorderT: TComboBox;
    chkBold: TCheckBox;
    chkItalic: TCheckBox;
    chkStrik: TCheckBox;
    chkUnder: TCheckBox;
    edColorBG: TColorBox;
    edColorBorder: TColorBox;
    edColorFont: TColorBox;
    edStyleType: TComboBox;
    LabelBorder: TLabel;
    LabelBorderB: TLabel;
    LabelBorderL: TLabel;
    LabelBorderR: TLabel;
    LabelBorderT: TLabel;
    LabelColorBg: TLabel;
    LabelColorBorder: TLabel;
    LabelColorFont: TLabel;
    LabelFontStyles: TLabel;
    LabelStyleType: TLabel;
    Panel1: TPanel;
    procedure edStyleTypeChange(Sender: TObject);
    procedure FormCreate(Sender: TObject);
    procedure FormShow(Sender: TObject);
  private
    procedure InitBorder(cb: TCombobox);
    procedure UpdateStyleEn;
    { private declarations }
  public
    { public declarations }
  end;


implementation

{$R *.lfm}

var
  msgBorderTypeNone: string = '无';
  msgBorderTypeSolid: string = '实线';
  msgBorderTypeDash: string = '虚线';
  msgBorderTypeDot: string = '点';
  msgBorderTypeDashDot: string = '虚线 点';
  msgBorderTypeDashDotDot: string = '虚线 点 点';
  msgBorderTypeSolid2: string = '实线2';
  msgBorderTypeSolid3: string = '实线3';
  msgBorderTypeWave: string = '波浪线';
  msgBorderTypeDouble: string = '双线';

procedure TfmLexerStyle.FormCreate(Sender: TObject);
begin
  ButtonPanel1.OKButton.Caption:= '确定';
  ButtonPanel1.CancelButton.Caption:= '取消';

  InitBorder(cbBorderL);
  InitBorder(cbBorderT);
  InitBorder(cbBorderR);
  InitBorder(cbBorderB);
end;

procedure TfmLexerStyle.edStyleTypeChange(Sender: TObject);
begin
  UpdateStyleEn;
end;

procedure TfmLexerStyle.FormShow(Sender: TObject);
begin
  UpdateFormOnTop(Self);
  FormCreate(nil);
  UpdateStyleEn;
end;

procedure TfmLexerStyle.InitBorder(cb: TCombobox);
var
  n: integer;
begin
  n:= cb.ItemIndex;
  with cb.Items do
  begin
    Clear;
    Add(msgBorderTypeNone);
    Add(msgBorderTypeSolid);
    Add(msgBorderTypeDash);
    Add(msgBorderTypeDot);
    Add(msgBorderTypeDashDot);
    Add(msgBorderTypeDashDotDot);
    Add(msgBorderTypeSolid2);
    Add(msgBorderTypeSolid3);
    Add(msgBorderTypeWave);
    Add(msgBorderTypeDouble);
  end;
  cb.ItemIndex:= n;
end;


procedure TfmLexerStyle.UpdateStyleEn;
var
  fmt: TecFormatType;
begin
  fmt:= TecFormatType(edStyleType.ItemIndex);
  edColorFont.Enabled:= fmt in [ftCustomFont, ftFontAttr, ftColor];
  edColorBG.Enabled:= true;

  chkBold.Enabled:= fmt in [ftCustomFont, ftFontAttr];
  chkItalic.Enabled:= chkBold.Enabled;
  chkUnder.Enabled:= false; //chkBold.Enabled; //it don't have effect
  chkUnder.Visible:= false;
  chkStrik.Enabled:= chkBold.Enabled;
end;

end.
