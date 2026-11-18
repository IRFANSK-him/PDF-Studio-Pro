; PDF Studio Pro educational Windows installer (Inno Setup 6)
#define AppName "PDF Studio Pro"
#define AppVersion "1.0.0-edu"
[Setup]
AppId={{8D97BA4E-8360-40F2-B7F8-69761D8D98A7}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\PDF Studio Pro
DefaultGroupName=PDF Studio Pro
OutputDir=..\installer-output
OutputBaseFilename=PDF-Studio-Pro-Setup-Educational
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
[Files]
Source: "..\dist\PDF-Studio-Pro\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\PDF Studio Pro"; Filename: "{app}\PDF-Studio-Pro.exe"
Name: "{autodesktop}\PDF Studio Pro"; Filename: "{app}\PDF-Studio-Pro.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Run]
Filename: "{app}\PDF-Studio-Pro.exe"; Description: "Launch PDF Studio Pro"; Flags: nowait postinstall skipifsilent
