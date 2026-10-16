Set WshShell = CreateObject("WScript.Shell")
Dim currentDir
currentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run "pythonw run_controller.py", 0, False
