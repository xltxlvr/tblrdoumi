@echo off
set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
pyinstaller --noconfirm tblrDoumi_windows.spec
%ISCC% tblrDoumi_setup.iss 
