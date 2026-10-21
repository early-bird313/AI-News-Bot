Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath & "\backend"
WshShell.Run """" & strPath & "\backend\.venv\Scripts\uvicorn.exe"" main:app --host 127.0.0.1 --port 8000", 0, False
Set WshShell = Nothing
