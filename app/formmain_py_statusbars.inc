{$ifdef nnnn}begin end;{$endif}

function PyHelper_StatusbarFromId(const H: Int64): TATStatus;
var
  Obj: TObject;
begin
  Result:= nil;
  if H<>0 then
  begin
    Obj:= TObject(PtrInt(H));
    if Obj is TATStatus then
      Result:= TATStatus(Obj)
    else
      MsgLogConsole('错误：statusbar_proc() 收到无效句柄，类型为 '+Obj.ClassName);
  end;
end;


