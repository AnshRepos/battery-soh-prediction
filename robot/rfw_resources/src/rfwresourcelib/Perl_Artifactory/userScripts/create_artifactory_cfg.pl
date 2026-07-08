#!/usr/bin/perl
#################################################################################################################################
#                                                                                                                               #
# FILE			:   create_artifactory_cfg.pl																					#
#                                                                                                                               #
# DESCRIPTION	: 	creates artifactory configuration file (see $cfg)															#
#                                                                                                                               #
# USAGE			:	perl create_artifactory_cfg.pl [-h] (update) -l|--location <fe|hi|hi-dev|kor|cob|szh|kis|bp|hc|pg>          #
#														-u|--user <userId> -p|--passwd <password> -useproxy                     #
#                                                                                                                               #
# COPYRIGHT		:   (c) 2015 Robert Bosch GmbH																					#
# HISTORY		:																												#
#                                                                                                                               #
# Date         	| Author                 		| Modification																	#
# 29.06.2015   	| M.Schoenfelder 	(ext)  		| Initial version																#
# 11.04.2015	| Saddam hussain A 	(RBEI/ECA2)	| Adapted to new configuration module, view content of configuration file added	#
# 21.06.2015    | Saddam hussain A 	(RBEI/ECA2)	| Adapted option to check and update .artifactory configuration with backward   # 
#                                                 compatibility- Story: 59498,                                                  #
#												  To add trust center separate script added, will be intergrated- story: 61588  #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled windows  and mac based execution : Feature-76330                      #
# 22.11.2016	| Sounak Patra (RBEI/ECA2)	    | Server selection based on user location										#
# 21.12.2016	| Sounak Patra (RBEI/ECA2)	    | Default server selection as 'hi' if user location	not found					#
# 27.01.2017	| Sounak Patra (RBEI/ECA2)	    | Fixed scenario when username is in uppercase									#
# 04.03.2017	| Sounak Patra (RBEI/ECA2)	    | Added Lund server url in server list											#
# 07.04.2017	| Sounak Patra (RBEI/ECA2)      | Changed lund server key from 'lud' to 'kis'									#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | Added Penang server url														#
# 07.03.2018	| Sounak Patra (RBEI/ECA2)      | Added Vietnam and Budapest Artifactory URL									#
# 12.04.2018	| Sounak Patra (RBEI/ECA2)		| Artifactory urls are updated to use https connection: story-246847			#
# 15.03.2019	| Sounak Patra (RBEI/ECQ2)		| Added noproxy option in curl                                                  #
#                                                                                                                               #
#################################################################################################################################	
# add the private includepathes
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use strict;
use artifactory_config;
use Getopt::Long;
use Net::Domain qw(hostdomain);
# Check env
if ( check_env() ) 
{
	write_error_log("\n===========================================================================================================\n\n");
	exit(1);
}

# Usage
my $usage = "
Usage:
  perl $0 [-h] ( update ) -l|--location <fe|hi|hi-dev|kor|cob|szh|kis|bp|hc|pg> -useproxy -u|--user <userId> -p|--passwd <password> -view

  Create Artifactory configuration file

       -h                      : Print helper message
        update                 : Update/Create artifactory configuration file
       -l     <serverLocation> : Artifactory Server location (optional for check, mandatory for create)
       -useproxy               : Uses current proxy settings
       -u     <userId>         : Artifactory User ID (optional for check, mandatory for create)
       -p     <password>       : Artifactory Password (optional for check, mandatory for create)
       -view                   : View artifactory configuration file content. Don't use it with other arguments
       	
  Arguments given in command line will be given more preferrence!
  Note: 
  	When no arguments given for check, will check for configuration file arguments.
  	When arguments given for check in command line, will be given priority to command line over configuration file
  	( can be used to check for access to artifactory for particular user without changing configuration file )
\n";

# global vars
my ( $check, $update );
my $cfg         = "";
my $noproxy     = "";
my $userId      = "";
my $server      = "";
my $password    = "";
my $result      = "errors";
my $location    = '';
my $view		= 0;
my $force		= 0;
my %serverSelect = (
		'fe'		=> "https://rb-cmbinex-fe-p1.de.bosch.com/artifactory",
        'hi'  		=> "https://rb-cmbinex-hi-p1.de.bosch.com/artifactory",
        'hi-dev01' 	=> "https://rb-cmbinex-hi-d01.de.bosch.com/artifactory",
        'kor' 		=> "https://rb-cmbinex-kor-p1.apac.bosch.com/artifactory",
        'cob' 		=> "https://rb-cmbinex-cob-p1.apac.bosch.com/artifactory",
        'szh'		=> "https://rb-cmbinex-szh-p1.apac.bosch.com/artifactory",
        'lud' 		=> "https://rb-cmbinex-lud-p1.emea.bosch.com/artifactory",
        'pg'		=> "https://rb-cmbinex-pg-p1.apac.bosch.com/artifactory",
        'bp'		=> "https://rb-cmbinex-bp-p1.emea.bosch.com/artifactory",
        'ev'		=> "https://rb-cmbinex-ev-p1.us.bosch.com/artifactory"
);
#`set _SET_ENV_AUTO_ANSWER=yes`;
my $autoAnswer   		= $ENV{_SET_ENV_AUTO_ANSWER};
my $defaultUser        	= "";

if ($^O =~ /mswin/i || $^O =~ /cygwin/i)
{
   $defaultUser        	= $ENV{USERNAME};
   $cfg					= "$ENV{USERPROFILE}\\\.artifactory" ;			# artifactory config file ( server, userId and password is stored here )
}
elsif ($^O =~ /linux/i)
{
   $defaultUser        	= $ENV{USER};
   $cfg					= "/home/$ENV{USER}/\.artifactory" ;
}
elsif ($^O =~ /darwin/i)
{
   $defaultUser        	= $ENV{USER};
   $cfg					= "/Users/$ENV{USER}/\.artifactory" ;	
}

$defaultUser = lc $defaultUser;
# Check for curl installation
$result = qx/curl -V/;
if ($result !~ /^curl/i) {
  	print "##################################################################################################################################";
  	print "# E r r o r\n";
  	print "# Curl is not installed!\n# Please install by command: <sudo apt-get install curl> for Linux and for windows download and install Curl executable\n";
  	print "##################################################################################################################################";
  	exit 1;
}

scanArgs();
create_config();

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Scan  input parameter
sub scanArgs
{
	my ($h, $useproxy);
	
	GetOptions(
  				'h'				=> \$h,
  				'l|location=s'	=> \$location,
   		        'useproxy'    => \$useproxy,
  				'u|user=s'		=> \$userId,
  				'p|passwd=s'	=> \$password,
  				'view'			=> \$view,
  				'force'			=> \$force	
  			) or do {
  						write_error_log("\nERROR: Extra or unknown argument or argument without value passed, check the usage.\n");
  						write_console( $usage );
						write_error_log("\n===========================================================================================================\n\n");
						exit(1);
  					}; 

	if(scalar @ARGV > 1 )
	{
		write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
		write_console( $usage );
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}

	if ( scalar @ARGV )
	{
		if ( $ARGV[0] =~ /^update$/i )
		{
			$update = 1;
		}
		else
		{
			write_error_log("\nERROR: Unknown arguments passed, check the usage.\n");
			write_console( $usage );
			write_error_log("\n===========================================================================================================\n\n");
			exit(1);
		}
	}

  	if ($h) 
  	{
  		write_error_log("\nINFO: Help message requested!\n");
   		write_console( $usage );
   		write_error_log("\n===========================================================================================================\n\n");
    	exit(0);
  	}
	
    if ($view)
    {
        if (-e $cfg)
        {
            viewConfig();
            exit(0);
        }
        else
        {
            write_error_log("\nERROR: $cfg not found. Can't view the content\n");
            exit(1);
        }
    }

    if (! -e $cfg)
    {
        write_complete_log("\nINFO: Configuration file: $cfg is not avilable, Creating configuration file\n\n");	
	}

  	if ( (not $userId) && ($password) ) 
  	{
  		write_error_log("\nERROR: Password cannot be specified alone.\n");
		write_console( $usage );
		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}

    if (!$location && ($userId && $password))
    {
        write_error_log("\nERROR: Kindly provide server location.\n");
        exit(1);
	}

    if ( $update && -e $cfg)
    {
        write_complete_log("\nDo you want to overwrite existing Artifactory config file: $cfg (y|n): ");
        if ( <STDIN> =~ /^y|yes$/i )
        {
            write_complete_log("INFO: Overwritting existing config file\n\n")
        }
        else
        {
            write_complete_log("INFO: Abort...\n");
            exit(0);
        }
        checkLocationArgument();
        $noproxy = ($useproxy ? "" : create_no_proxy($server));
        checkUserPasswordArgument();
	}
    else
	{
        if ( $update)
        {
            write_complete_log("\nINFO: Update can't be possible as $cfg file doesn't exist\n");
		}
        checkLocationArgument();
        $noproxy = ($useproxy ? "" : create_no_proxy($server));
        checkUserPasswordArgument();
    }
}

#################################################################################################################
# location argument check- Story: 59498
#
sub checkLocationArgument
{
	my (@domainName, $hostName);

	if ( !$location )
  	{
  		if (hostdomain && scalar(split(/\./, hostdomain)))
  		{
  			@domainName = split(/\./, hostdomain);
			$hostName = $domainName[0];
			$hostName = lc $hostName;
  		}
  		else
  		{
  			write_console("\nCurrent domain not found: Selecting domain as 'hi'\n");	
  			$hostName = 'hi' 			
  		} 
  		
  		foreach my $key (keys %serverSelect)
  		{
    		printf( "%-13s$serverSelect{$key}\n", "($key)" );
  		}
  		my @keys = keys %serverSelect;
 		if ( grep { $_ eq $hostName } @keys )
		{
			print "\nDefault: $serverSelect{$hostName}\n";
  			printf("\nSelect Server %10s : ", "[$hostName]");
		}
		else
		{
			$hostName = 'hi';
			print "\nDefault: $serverSelect{$hostName}\n";
  			printf("\nSelect Server %10s : ", "[$hostName]"); 
		}
  		chomp($location = <STDIN>);
  		if ($location eq "")          
  		{ 	
  			$server = $serverSelect{$hostName};	
  			$location = $hostName
  		}
  	}
  	if ( $serverSelect{$location} ) 
  	{ 
  		$server = $serverSelect{$location};
  	}
  	else
  	{
  		write_error_log("\nERROR: Given location not available or not valid, check and given valid location as [hi|hi-dev|kor|kob|szh] (any one location can be given)\n");
  		write_console( $usage );
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	$server = $serverSelect{$location};
}

#################################################################################################################
# user and password argument check- Story: 59498
#
sub checkUserPasswordArgument
{
  	if ( ! $userId )
  	{
  		printf("\nSelect User   %10s : ", "[$defaultUser]");
  		chomp(my $selection = <STDIN>);
  		$selection = lc $selection;
  		($selection ne "") ? ( $userId = $selection ) : ( $userId = $defaultUser )
  	}
  	if ( ! $password)
	{
    	print "\nEnter PWD required to get encrypted password string from artifactory\n";
    	printf("\nPassword      %10s : ", "");
    	
    	if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i)
    	{
    		system('stty -echo');  # Disable echoing
    		chomp($password = <STDIN>);
    	}
    	elsif ($^O =~ /mswin/i)
    	{
   			$password = get_win_password($password)
    	}
    	
    	while(1)
    	{
    		if ( $password eq "")
    		{
    			print "Password not specified\nEnter again: ";
				if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i){
					chomp($password = <STDIN>); 
				}
				elsif ($^O =~ /mswin/i){
					$password = get_win_password($password)
				}
    		}
    		else
    		{
    			last;
    		}
    	}
    	system('stty echo') if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i);   # Turn it back on
    	print "\n\n";
    	check_https($serverSelect{$location}, $userId, $password, $noproxy);
	}
}

#################################################################################################################
# view artifactory configuration file- Story: 59498
#
sub viewConfig
{
	open(CONFIG, "<$cfg") or die "Configuration file: $cfg cannot be opened!\n\n===========================================================================================================\n\n";
	print "\nArtifactory configuration file: $cfg content\n---------------------------------------------------------------------\n";
    print "$_" foreach ( <CONFIG> );
    print "\n";
    close(CONFIG);
}

#################################################################################################################
# Create .artifactory config file
#
sub create_config
{
    my $ping_status = ping_server($server, $noproxy);
    if ($ping_status)
    {
        write_error_log( "ERROR: Aborting..." );
        exit(1);
    }
    print "Getting encrypted password...\n";
    my $enc_pwd = get_encrypted_password($server, $userId, $password, $noproxy);
    if ( $enc_pwd == 1 )
    {
        write_error_log( "ERROR: Artifactory config creation was not successful.\n" );
        exit(1);
    }
    else
    {
        write_to_config($server, $userId, $enc_pwd, $noproxy, $cfg);
        write_error_log( "\nINFO: Artifactory config successfully written to $cfg\n" );
        exit(0);
    }
}
