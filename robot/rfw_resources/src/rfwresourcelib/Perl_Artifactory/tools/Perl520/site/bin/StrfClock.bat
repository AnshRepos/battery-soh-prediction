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

=head1 NAME

StrfClock - a Tk based clock.

=head1 SYNOPSIS

StrfClock <options> [strftime time formats]

=head1 DESCRIPTION

This pops up a Tk based digital clock that can be used to display the
current date and time in various formats based on strftime.

This script is based on, and is part of, the Perl L<Tk::Month> module.

=head1 OPTIONS

Most of these options correspond to the configuration options of the
module L<Tk::StrfClock>.

=head1 SEE ALSO

See also Perl module L<Tk::Month>.

=head1 COPYRIGHT

Copyright (c) 1998-2014 Anthony R Fletcher. All rights reserved.
This script is free software; you can redistribute them and/or modify
them under the same terms as Perl itself.

This code is supplied as-is - use at your own risk.

=cut

use 5;
use warnings;
use strict;

use Tk::StrfClock qw(StrfClock);
StrfClock(@ARGV);

1;


__END__
:endofperl
