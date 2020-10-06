
; #define MyAppName "X"
; #define MyAppVersion "1.0"
; #define UpdaterFolder "Updater"
; #define SettingsFile "settings.json"
; #define LauncherName "launcher.exe"
; #define ServiceName "service.exe"
; #define BuildDir "build"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}_{#MyAppVersion}_setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#BuildDir}\{#UpdaterFolder}\{#ServiceName}";	DestDir: "{app}\{#UpdaterFolder}";	Flags: ignoreversion uninsrestartdelete
Source: "{#BuildDir}\{#UpdaterFolder}\{#SettingsFile}";	DestDir: "{app}\{#UpdaterFolder}";	Flags: ignoreversion uninsrestartdelete
Source: "{#BuildDir}\{#LauncherName}";	                DestDir: "{app}";                   Flags: ignoreversion uninsrestartdelete
Source: "{#BuildDir}\{#MyAppName}\*";	                DestDir: "{app}\{#MyAppName}";		Flags: ignoreversion recursesubdirs createallsubdirs uninsrestartdelete

[Icons]
Name: "{commondesktop}\{#MyAppName}";	Filename: "{app}\{#LauncherName}";	Tasks: desktopicon

[Registry]
Root: HKLM64; Subkey: "Software\{#MyAppName}";            Flags: noerror uninsdeletekey
Root: HKLM64; Subkey: "Software\{#MyAppName}\Updater";    Flags: noerror
Root: HKLM64; Subkey: "Software\{#MyAppName}\Updater";    ValueType: string; ValueName: "settings"; \
			ValueData: "{app}\{#UpdaterFolder}\{#SettingsFile}"; Flags: noerror
Root: HKLM64; Subkey: "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"; \
			ValueType: String; ValueName: "{app}\{#LauncherName}"; ValueData: "RUNASADMIN"; \
			Flags: uninsdeletevalue;

[Run]
Filename: "{app}\{#UpdaterFolder}\{#ServiceName}"; Parameters: "--startup delayed install";	\
		Flags: "runhidden runascurrentuser"; WorkingDir: "{app}\{#UpdaterFolder}"; StatusMsg: "Installing Service..."
Filename: "{app}\{#UpdaterFolder}\{#ServiceName}"; Parameters: "start"; \
		Flags: "runhidden runascurrentuser"; WorkingDir: "{app}\{#UpdaterFolder}"; StatusMsg: "Starting Service..."
Filename: "{app}\{#LauncherName}"; Description: "Run the launcher"; Flags: "postinstall runascurrentuser"