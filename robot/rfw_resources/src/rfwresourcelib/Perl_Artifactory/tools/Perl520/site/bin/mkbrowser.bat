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
#!/usr/bin/perl -w
#line 15

# $Id: mkbrowser,v 1.5 2004/02/11 23:51:07 kiesling Exp $

=head1 NAME

  mkbrowser - Create Tk::Browser object and open its window.

=head1 SYNOPSIS

     # mkbrowser <module_pathname>  # Open a library file by name
     # mkbrowser <package_name>     # Open package(s) matching
                                    # <package_name> (Unix specific);
     # mkbrowser                    # Browse the entire library.
 

=head1 DESCRIPTION

Mkbrowser creates a Tk::Browser object and opens its
window. Tk::Browser(3) describes browser objects in detail.

=head1 SEE ALSO

perl(1), Tk::Browser(3), Tk(1)

=head1 VERSION INFO

$Id: mkbrowser,v 1.5 2004/02/11 23:51:07 kiesling Exp $ 

Written by Robert Kiesling, rkies@cpan.org.

Copyright © 2001-2004 by Robert Kiesling.  Licensed using the same
terms as Perl.  Refer to the file, "Artistic," for details.

=cut

use Tk;
use Tk::Browser;
#use Browser::LibModule qw(new retrieve readlib basename DESTROY);
use Browser::LibModule;

my $b;

$b = new Tk::Browser;
if ($#ARGV < 0) { # No args.
      $b -> open;
  } else {
      if ( -e $ARGV[0] ) { # file name;
	  $b -> open(pathname => $ARGV[0]);
      } else { # Try a package name
	  $b -> open(package => $ARGV[0]);
      }
  }


MainLoop;

__END__
:endofperl
