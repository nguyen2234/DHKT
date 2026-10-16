; Script Inno Setup 6 cho CÔNG CỤ TẠO BÁO CÁO WO
; Dùng để đóng gói thư mục dist\WOReportTool thành file cài đặt duy nhất WOReportTool_Setup.exe

#define MyAppName "Công cụ tạo báo cáo WO"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NAN_DHKT"
#define MyAppExeName "WOReportTool.exe"

[Setup]
; Thông tin định danh ứng dụng
AppId={{5E97D453-8A2F-4C8D-9134-219C0E35AA8F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=WOReportTool_Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy toàn bộ file đã build từ thư mục dist\WOReportTool
Source: "..\dist\WOReportTool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"

[Run]
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
