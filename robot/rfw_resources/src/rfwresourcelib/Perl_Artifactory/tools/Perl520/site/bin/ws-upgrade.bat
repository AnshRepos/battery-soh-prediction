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

  ws-upgrade -- Upgrade a workspace.

=head1 SYNOPSIS

  ws-upgrade <workspace-file-names>

=head1 DESCRIPTION
  
Makes a new version of <workspace> that is compatible
with the installed version of Tk::Workspace.pm.  
The pre-upgrade workspace is saved with the extension ".old,"
and the text itself is saved to "<workspace-name>.txt."

=head1 CREDITS

  Robert Allan Kiesling <rkiesling@earthlink.net>

=cut

require Carp;
require Tk::Workspace;

if( @ARGV < 1 ) { 
	print "usage: ws-upgrade <workspaces>\n";
	exit( 1 );
}

my ($text, $l);
# 0 = line(s) before my $text = ... inclusive,
# 1 = text to save;
# 2 = line(s) after end-of-text inclusive
my $s;
my @ws = &Tk::Workspace::workspaceobject;
my $wsolen = @ws;
my $basename;
my $i;
foreach( @ARGV ) {
  $basename = $_;
  open W, "<$basename" or die "Couldn't open $basename: $!\n";
  open T, ">$basename.txt" or die "Couldn't open $basename.txt: $!\n";
  $state = 0;
  print "Renaming \"$_\" to \"$_.old.\"\n";
  rename $basename, "$basename.old";
  print "Saving text to \"$basename.txt.\"\n";
  open WNEW, ">$basename" or die "Couldn't open $basename: $!\n";
  printf WNEW $ws[0]."\n";
  printf WNEW 'my $text = <<\'end-of-text\';' . "\n";
 LINE:
  while ( $l = <W> ) {
    if( $s == 0 && $l =~ /my \$text \= \<\<\'end-of-text\'/ ) {
      $s = 1;
      next LINE;
    }
   if( $s == 1  && $l !~ /end-of-text/) {
     printf T $l;
     printf WNEW $l;
   }
   if( $l =~ /end-of-text/ ) {
     $s = 2;
   }
  }
  close W;
  close T;
  printf WNEW "end-of-text\n";
  
  grep { s/name\=\'\'/name=\'$basename\'/ } @ws;
  for( $i = 2; $i < $wsolen; $i++ ) {
     printf WNEW $ws[$i]."\n";
  }
  close WNEW;
  system( "chmod +x $basename" );
}

__END__
:endofperl
