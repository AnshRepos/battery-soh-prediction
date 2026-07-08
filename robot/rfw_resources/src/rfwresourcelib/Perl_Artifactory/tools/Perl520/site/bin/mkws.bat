@rem = '--*-Perl-*--
@echo off
if "%OS%" == "Windows_NT" goto WinNT
perl -x -S "%0" %1 %2 %3 %4 %5 %6 %7 %8 %9
goto endofperl
:WinNT
perl -x -S %0 %*
if NOT "%COMSPEC%" == "%SystemRoot%\system32\cmd.exe" goto endofperl
if %errorlevel% == 9009 echo You do not have Perl in your PATH.
if errorlevel 1 goto script_failed_so_exit_with_non_zero_val 2>nul
goto endofperl
@rem ';
#!perl 
#line 15

# mkws -- Workspace launcher
# Substitute path of the perl binary on your system
# in the line above.
# When installing, change permissions to executable
# using 'chmod +x mkws'.  

use Tk;
use Tk::Workspace;

my $name;

if ( defined @ARGV ) {
	$name = $ARGV[0];
	} else {
	$name = 'workspace'
}
# If you place Workspace.pm in the current directory, 
# us: 'Workspace::open(Workspace::create($name));

Tk::Workspace::open(Tk::Workspace::create($name));

__END__
:endofperl
