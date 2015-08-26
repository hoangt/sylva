@echo off
set TERMINAL=C:\Users\Administrator\Dropbox\sylva\misc\conemu\ConEmu64.exe
set EXECPY=C:\Users\Administrator\Dropbox\sylva\misc\exec.py
set PYTHON27=c:\python27\python.exe
set WINDOWTITLE="SYLVA - System Architectural Synthesis Framework"

if "%1"=="" goto a else if exist %1 goto b

:a
start %TERMINAL% /title %WINDOWTITLE%^
/cmd %PYTHON27% %EXECPY% -new_console:t:"SYLVA"
goto end

:b
start %TERMINAL% /title %WINDOWTITLE%^
 /cmd %PYTHON27% %EXECPY% -new_console:t:"SYLVA" -script "%1"

:end
