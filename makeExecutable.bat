@echo off

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller Dler.spec
if not exist binaries mkdir binaries
copy dist\*.exe binaries
