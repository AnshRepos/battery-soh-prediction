#################################################################################################################
#
# FILE:          deploy_debian.pl
#
# DESCRIPTION:   Deploy/Upload a debian package to an artifactory repository
#
# USAGE:         deploy_file.pl -u <usr_id> -p <pwd> -f <debian_src> -t <target_folder> [-s <server>] -r <repo>
#
# ARGUMENTS:     - debian source package
#                - distribution
#                - component
#                - user id (optional, will be read from config file)
#                - password (optional, will be read from config file)
#                - server (optional, will be read from config file)
#                - repository
#
# COPYRIGHT:     (c) 2014 Robert Bosch GmbH
# HISTORY:
#
# Date         | Author                 | Modification
# 23.10.2014   | M.Schoenfelder (ext)   | Initial version
# 06.11.2014   | M.Schoenfelder (ext)   | do not store package in pool dir, could not be read from apt-get 
# 22.06.2015   | M.Schoenfelder (ext)   | adapt to new config file
# 14.09.2015   | M.Schoenfelder (ext)   | do not allow spaces for -c, -d, -a
#################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use Getopt::Std;

# Global variables
# Usage
my $Usage = "
Usage:
  perl $0 [-h] -r <repo> -f <debian_src> -d <distribution> -c <component> -a <architecture> [-s <server>] [-u <usr_id> -p <pwd>]

  Deploy a local debian package to an Artifactory repository.

       -h                   : Print this usage text.

       -r <repo>            : Artifactory Repository
       -f <debian_src>      : Debian source package
       -d <distribution>    : Debian package distribution
       -c <component>       : Debian package component name
       -a <architecture>    : Debian package architecture
       -s <server>          : Artifactory Server (optional, will be read from config file)
       -u <usr_id>          : Artifactory User ID (optional, will be read from config file)
       -p <pwd>             : Artifactory Password (optional, will be read from config file)
       
       It is not possible to deploy artifacts with spacing in names, so do not use spaces in options -d, -c and -a.
\n";

# arguments
my $usr_id      = "";
my $pwd         = "";
my $debian_src  = "";
my $dist        = "";
my $comp        = "";
my $arch        = "";
my $server      = "";
my $repo        = "";

# Check env
if ( check_env() ) 
{
	write_error_log("\n===========================================================================================================\n\n");
	exit(1);
}

# Read arguments
scan_args();

# check if source file exists
if (! -f $debian_src) {
    print "ERROR: source file $debian_src does not exist.\n";
    exit(1);
}

# generate checksums
my $md5_value  = `md5sum $debian_src`;
my $sha1_value = `sha1sum $debian_src`;

# remove heading slash (windows)
$md5_value  =~ s/\A\\//;
$sha1_value =~ s/\A\\//;

$md5_value  = substr($md5_value,0,32);
$sha1_value = substr($sha1_value,0,40);

# target info
my $file_name   = basename($debian_src);

print "INFO: Uploading $debian_src to $server/$repo\n";
my $cmd  = "curl -i -X PUT -u $usr_id:$pwd -H \"X-Checksum-Md5: $md5_value\" ";
   $cmd .= "-H \"X-Checksum-Sha1: $sha1_value\" -T \"$debian_src\" ";
   $cmd .= "\"$server/$repo/$file_name;deb.distribution=$dist;deb.component=$comp;deb.architecture=$arch\"";
system($cmd);

exit(0);

#################################################################################################################
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly
#
sub scan_args
{
  my %opts = ();
  getopts('hu:p:f:d:c:a:s:r:',\%opts);

  if ( ($opts{h}) ) {
    print $Usage;
    exit(0);
  }

  if ( (not $opts{r}) || (not $opts{f}) || (not $opts{d}) || (not $opts{c}) || (not $opts{a})) {
    print "ERROR: Arguments missing!\n";
    print $Usage;
    exit(1);
  }

  if ( (not $opts{u}) && ($opts{p}) || (not $opts{p}) && ($opts{u})) {
    print "User and PWD have to be given both or none of them.\n";
    print $Usage;
    exit(1);
  }

  # set vars from mandatory arguments
  $debian_src   = $opts{f};
  $dist         = $opts{d};
  $comp         = $opts{c};
  $arch         = $opts{a};
  $repo         = $opts{r};
  
  # check for spaces in artifact folder names
  if ( $dist =~ /\s/ || $comp =~ /\s/ || $arch =~ /\s/) {
    print "ERROR: artifactory folders shall not contain spaces, please check arguments (-d, -c, -a)\n";
    exit(1);
  }
  # read server from standard config file
  my $result = "";
  ($result,$server,$usr_id,$pwd) = read_from_config();
  # all the return codes will be consolidated into one, after checking possibilites in future release
  #if ($result eq "1") {print "No script execution because of errors, no erro code on request -> exit with status 0\n";exit(1);}    # requested not to exit with errors in order to continue calling scripts
  if ($result eq "1") {print "Script $0 aborted, exit with status 1\n";exit(1);}    # exit with error
  if ($result eq "2") {print "Script $0 aborted, exit with status 1\n";exit(1);}    # exit with error
  # overwrite with argument settings if available
  $server   = $opts{s} if ($opts{s});
  $usr_id   = $opts{u} if ($opts{u});
  $pwd      = $opts{p} if ($opts{p});
}
