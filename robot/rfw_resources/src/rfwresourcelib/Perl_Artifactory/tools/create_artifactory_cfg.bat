@echo off
set "path=%CD%\Perl520\bin;%path%"
set "perl_home=%CD%\Perl520\bin"
set "path=%path%;%CD%\curl-7.50.3\bin"
set PARENTPATH=%~dp0
set PARENTPATH=%PARENTPATH:~0,-7%
@echo on

perl %PARENTPATH%\userScripts\create_artifactory_cfg.pl %*
