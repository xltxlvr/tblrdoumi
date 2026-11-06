[Setup]
AppId={{c7838ad8-3f48-412e-b5c8-46b708482793}
AppName=tblr Doumi
AppVersion=3.9.10.1
DefaultDirName={localappdata}\Programs\tblrDoumi
DefaultGroupName=nvLatexApps
OutputDir=output
OutputBaseFilename=tblrDoumiSetupR3-9

[Registry]
Root: HKCR; Subkey: ".tblr"; ValueType: string; ValueName: ""; ValueData: "tblrfile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "tblrfile"; ValueType: string; ValueName: ""; ValueData: "Tblr File"
Root: HKCR; Subkey: "tblrfile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\tblrdoumi.ico"
Root: HKCR; Subkey: "tblrfile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\tblrDoumi.exe"" ""%1"""

[Files]
; 앱 실행 파일 및 모든 서브 폴더 복사
Source: "dist\tblrDoumi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; [추가] 배포 패키지 빌드 경로 내의 templates 폴더를 설치 폴더({app}\templates)로 복사
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "tblrdoumi.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\tblrDoumi"; Filename: "{app}\tblrDoumi.exe"
Name: "{commondesktop}\tblrDoumi"; Filename: "{app}\tblrDoumi.exe"

[Code]
// 1. 기존 버전 언인스톨 관련 로직
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  // AppId 기반으로 레지스트리에서 언인스톨 경로 탐색 (현재 유저 및 로컬 머신 모두 확인)
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{c7838ad8-3f48-412e-b5c8-46b708482793}_is1';
  sUnInstallString := '';
  
  if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString);
    
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    // 기존 버전 사일런트 삭제 진행 (/SILENT 옵션)
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

// 설치 프로세스 단계 변경 시 호출되는 내장 함수
procedure CurStepChanged(CurStep: TSetupStep);
begin
  // 실제 파일 복사가 이루어지는 Install 단계 직전에 기존 버전 삭제 수행
  if (CurStep = ssInstall) then
  begin
    if IsUpgrade() then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

// 2. 언인스톨 시 환경변수(PATH)를 깔끔하게 제거하는 로직
procedure RemovePathEnv(PathToRemove: string);
var
  Paths: string;
  P: Integer;
begin
  if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Paths) then
  begin
    // 경로의 앞뒤 공백 및 세미콜론 매칭을 위해 포맷팅 후 검색
    P := Pos(';' + Uppercase(PathToRemove) + ';', ';' + Uppercase(Paths) + ';');
    if P = 0 then
    begin
      P := Pos(';' + Uppercase(PathToRemove) + '\;', ';' + Uppercase(Paths) + ';');
    end;

    if P > 0 then
    begin
      // 매칭된 경로 부분 삭제
      Delete(Paths, P - 1, Length(PathToRemove) + 1);
      
      // 첫 번째 문자가 세미콜론이면 제거
      if (Length(Paths) > 0) and (Paths[1] = ';') then
        Delete(Paths, 1, 1);
        
      RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', Paths);
    end;
  end;
end;

// 언인스톨 프로세스 단계 변경 시 호출되는 내장 함수
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // 앱이 설치되었던 디렉토리를 PATH에서 완전히 제거
    RemovePathEnv(ExpandConstant('{app}'));
  end;
end;
