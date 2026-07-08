@echo off
echo ^+-----------------------------------------------------^+
echo ^|  Check required modules are installed or not        ^|
echo ^+-----------------------------------------------------^+
echo.

if not exist "C:\Users\%USERNAME%\.artifactory" (
	echo Missing ".artifactory" config file, please execute "perl create_artifactory_cfg.pl update" to create .artifactory file
) else (
	echo Found .artifactory file
)

where perl.exe>nul 2>nul
if %errorlevel%==1 (
    echo perl.exe check ... Failed, perl is not installed
	IF EXIST %CD%\Perl520\bin (
	echo Adding path of perl.exe to system variables...
	set "path=%CD%\Perl520\bin;%path%"
	set "perl_home=%CD%\Perl520\bin"
	) ELSE (
	echo ERROR: Cannot find perl.exe. Please make sure the package exists in same directory
	)	
) else (
	call:checkVersion perl.exe 5.20	
)

where curl.exe>nul 2>nul
if %errorlevel%==1 (
    echo curl.exe check ... Failed, curl is not installed
	IF EXIST %CD%\curl-7.50.3\bin (
	echo Adding path of curl.exe to system variables...
	set "path=%path%;%CD%\curl-7.50.3\bin" 
	) ELSE (
	echo ERROR: Cannot find curl.exe. Please make sure the package exists in same directory
	)
) else (
	call:checkVersion curl.exe 7.22
)

CMD /k
GOTO:EOF

:checkVersion
REM -------------------------------------------------------------
REM check version
REM -------------------------------------------------------------
@for %%i in (%1) do @set file_path=%%~$PATH:i
set file_path=%file_path:\=\\%
for /F "tokens=2 delims==" %%I in (
  'wmic datafile where "name='%file_path%'" get version /format:list'
) do set "RESULT=%%I"
if %RESULT% GEQ %2 (
	echo %1 check ... Passed
) else (
	echo %1 check ... Failed, version is older than %2
)
GOTO:EOF