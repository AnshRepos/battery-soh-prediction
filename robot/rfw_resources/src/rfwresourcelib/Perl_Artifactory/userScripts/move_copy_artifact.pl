#########################################################################################################################################
#																																		#
# FILE			:	move_artifact.pl																									#
#																																		#
# DESCRIPTION	:   Move a file/folder from one artifactory repository to another														#
#																																		#
# USAGE			:   move_copy_artifact.pl [ -h ] ( -move | -copy ) -f <configFile> | -r <sourceRepo> -c <sourceComponent>				# 
#					-t <targetRepo> -d <targetComponent> [ -dryRun ] [ -s <server> -u <userId> -p <password> -useproxy ]                #
#																																		#
# ARGUMENTS		:   See usage																											#
#																																		#
# COPYRIGHT		:   (c) 2014 Robert Bosch GmbH																							#
# HISTORY		:																														#
#																																		#
# Date         	| Author                 		|  Modification																			#
# 07.11.2014   	| M.Schoenfelder (ext)   		|  Initial version																		#
# 22.06.2015   	| M.Schoenfelder (ext)   		|  adapt to new config file																#
# 10.02.2016	| Saddam Hussain A (RBEI/ECA2)	|  Feature added to change destination component ( Story-48924 )						#
#												   Adapted to new configuration module													#
#												   Config file added to perform operation for more than one artifact copy or move.		#	
#												   Logger feature has been added to log output											#
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		|  Modified code to handle empty line with spaces in config file				 		#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      |  Made modifications to check latest script version: story-165111						#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		|  Added feature to stop execution of older scripts: story-185699						#
# 20.03.2019	| Sounak Patra (RBEI/ECQ2)		|  Added noproxy option in curl                                                         #
#																																		#
#########################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use strict;
use artifactory_config ( 'read_from_config', 'check_env', 'create_log_file', 'write_console', 'write_complete_log',
                         'write_error_log', 'normalise_path', 'check_settings' );
use Getopt::Long;
use JSON qw( decode_json );
use Data::Dumper;

# Usage

my $usage = 
{
	'header'			=>	'Usage:',
	'prefixArguments' 	=> "perl $0",
	'allArguments' 		=> '[ -h ] ( -move | -copy ) -f <configFile> | -r <sourceRepo> -c <sourceComponent> -t <targetRepo> -d <targetComponent> [ -dryRun ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'moveArguments'		=> ' -move -f <configFile> | -r <sourceRepo> -c <sourceComponent> -t <targetRepo> -d <targetComponent> [ -dryRun ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'copyArguments' 	=> ' -copy -f <configFile> | -r <sourceRepo> -c <sourceComponent> -t <targetRepo> -d <targetComponent> [ -dryRun ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'content' 			=> 'Recursively move/copy content.',

	'description' 		=>
		{  
			'1'  => { '-h' 			=>  '-h                       : Print this usage text.',},
    		'2'  => { '-move' 		=>  '-move <move>             : For move artifact',},
    		'3'  => { '-copy' 		=>  '-copy <copy>             : For copy artifact'},
    		'4'  => { '-r' 			=>  '-r    <sourceRepo>       : Artifactory source repository'},
    		'5'  => { '-t'          =>  '-t    <targetRepo        : Artifactory target repository'},
    		'6'  => { '-c' 			=>  '-c    <sourceComponent>  : Component (relative path of file/folder inside repository to be moved/copied)'},
    		'7'  => { '-d'          =>  '-d    <targetComponent   : TargetComponent (if not given source component structure( path ) will be maintained'},
    		'8'  => { '-f' 			=>  '-f    <configFile>       : Config file with source component information'},
    		'9'  => { '-dryRun'     =>  '-dryRun                  : Test run'},
    	   '10'  => { '-s' 			=>  '-s    <server>           : Artifactory Server (optional, will override config file)'},
    	   '11'  => { '-u' 			=>  '-u    <userId>           : Artifactory User ID (optional, will override config file)'},
    	   '12'  => { '-p' 			=>  '-p    <password>         : Artifactory Password (optional, will override config file)'},
           '13'  => { '-useproxy' =>  '-useproxy                : Uses current proxy settings (optional, will override config file)'}
		},
    'endContent' => 'Other arguments will be ignored when using -f
    	Format of <config_file>:
				# used with comments
				# one line per move/copy; items seperated by two colon; all arguments except targetComponent are mandatory
				sourceRepository::targetRepository::sourceComponent::targetComponent
       	
				When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!',
};
# arguments
my ( $server, $userId, $password, $repository_name, $no_proxy );
my ($copy, $move, $action, $dryRun, $dry, $configFile );

# other arguments
my $auto_answer   				= $ENV{_SET_ENV_AUTO_ANSWER};
my $moveCopyLogFile 			= 'move_copy.log';
my $errorLogFile				= 'move_copy_error.log';
my $startTime					= time();
my $endTime						= 0;
my $configFileArgumentCount		= 4;
my (%argumentList,$errorString) ;

my ( $componentCount, $executedComponentCount, $executedArtifactCount, $executedFolderCount, $failedExecuteComponentCount ) = ( 0,0,0,0,0);

# Create log file
my $artifactoryLogDir = create_log_file( $moveCopyLogFile,$errorLogFile );
exit(1) if( $artifactoryLogDir == 1 );

# Check env
if ( check_env() ) 
{
	write_error_log("\n===========================================================================================================\n\n");
	exit(1);
}

# Read arguments
scanArgs();
# Validates script version
validate_script_version($server, $userId, $password, $repository_name, $no_proxy);
# Dry run
$dry = '&dry=1' if $dryRun; 

( $move ) ? ( $action = 'move' ) : ( $action = 'copy' );
write_error_log("On server\t: $server\nOperation\t: \u$action\n");

$componentCount	= (keys %argumentList);
NEXT: foreach my $artifact (keys %argumentList)
{
	if (!$argumentList{$artifact}{targetComponent}) 
  	{
  		write_error_log("\nINFO: target component not given, source folder structure will be maintained!\n");
  	}
  	
	if( check_settings( $server, $userId, $password, $argumentList{$artifact}{sourceRepo}, $no_proxy ) ) 					# source repository existence check
	{
		my 	$writeString = "\nERROR: Source repository not found or user not having read permission to ";
        $writeString .= "repository: $argumentList{$artifact}{sourceRepo}\n\n";
    	write_error_log($writeString);
    	$errorString .= $writeString;
    	next NEXT;
	}
	
	if( check_settings( $server, $userId, $password, $argumentList{$artifact}{targetRepo}, $no_proxy ) )				# target repository existence check
	{
		my 	$writeString = "\nERROR: Target repository not found or user not having read permission to ";
        $writeString .= "repository: $argumentList{$artifact}{sourceRepo}\n\n";
    	write_error_log($writeString);
    	$errorString .= $writeString;
    	next NEXT;
	}
	if ( $argumentList{$artifact}{sourceComponent} ne $argumentList{$artifact}{targetComponent} )
	{
		my @sourceComponentPath = split '/', $argumentList{$artifact}{sourceComponent};
		my $pomFile = "$sourceComponentPath[$#sourceComponentPath-1]-$sourceComponentPath[$#sourceComponentPath]\.pom";

        my $getPom = set_curl_command($no_proxy, $userId, $password, 0);		
        $getPom .= "-s -X GET -H \"application/vnd.org.jfrog.storage.StatsInfo+json\" ";
        $getPom .= "\"$server/api/storage/$argumentList{$artifact}{sourceRepo}/$argumentList{$artifact}{sourceComponent}/$pomFile\"";
		my $getPomOutput = `$getPom`;
		my $decodeGetPomOutput = decode_json($getPomOutput);

		unless ( defined $$decodeGetPomOutput{'errors'} )
		{
			write_error_log("\nWhile Move/Copy artifact, groupId, artifactId and verison cannot be changed, same should be used.\n");
			$errorString .= "\nWhile Move/Copy artifact, groupId, artifactId and verison cannot be changed, same should be used.\n";
			$failedExecuteComponentCount++;
			next NEXT;
		}
	}

    my $moveCopyCmd = set_curl_command($no_proxy, $userId, $password, 0);
    $moveCopyCmd .= "-s -X POST -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.CopyOrMoveResult+json\" ";
    $moveCopyCmd .= "\"$server/api/$action/$argumentList{$artifact}{sourceRepo}/$argumentList{$artifact}{sourceComponent}";
    $moveCopyCmd .= "\?to=/$argumentList{$artifact}{targetRepo}/$argumentList{$artifact}{targetComponent}$dry\"";
	my $moveCopyOutput = `$moveCopyCmd`;
	my $decodeMoveCopyOutput = decode_json($moveCopyOutput);
	# Example output for moving artifact
	#{
	#	"messages" : [ {
	#	"level" : "INFO", or "ERROR"
	# 	"message" : "moving test-release:g/a/1.0 to test-repo:g/a/1.0 completed successfully, 20 artifacts and 9 folders were moved"
	#	} ]
	#}
	if ($decodeMoveCopyOutput->{messages}[0]{level} =~ /ERROR/i)
	{ 
			write_complete_log("\n\u$action $argumentList{$artifact}{sourceRepo}/$argumentList{$artifact}{sourceComponent}==>$argumentList{$artifact}{targetRepo}/$argumentList{$artifact}{targetComponent} - FAILED\n");
			$errorString 	   	   .= "ERROR: Message: $decodeMoveCopyOutput->{messages}[0]{message}\n";
			$failedExecuteComponentCount++;
	}
	else
	{
		if ( not $dryRun)
		{
			write_complete_log("\n\u$action $argumentList{$artifact}{sourceRepo}/$argumentList{$artifact}{sourceComponent}==>$argumentList{$artifact}{targetRepo}/$argumentList{$artifact}{targetComponent} - OK\n");
			my $stringToParse 		= $decodeMoveCopyOutput->{messages}[0]{message};
			$stringToParse 			=~ /\S+,\s*(\d+)\s*artifacts\s*and\s*(\d+)\s*folders/;
			$executedArtifactCount += $1;
			$executedFolderCount   += $2;
			$executedComponentCount++;
		}
		else
		{
			my 	$writeString 		= "\n\u$action $argumentList{$artifact}{sourceRepo}/$argumentList{$artifact}{sourceComponent}==>$argumentList{$artifact}{targetRepo}/$argumentList{$artifact}{targetComponent}";
				$writeString 	   .= "\n\t\t$decodeMoveCopyOutput->{messages}[0]{message}\n\n";
			write_complete_log($writeString);
		}
	}
}

# Calculate time to complete promotion
$endTime 			= time();
my $duration 		= $endTime - $startTime;
my $minutes 		= int ( ( $duration / 60 ) % 60 );
my $seconds 		= $duration % 60;
my $hours 			= int( ( $duration /60) / 60 );
# Check for intermediate errors and exit
if ($errorString ne "") 
{
	my 	$writeString  = "";
  	   	$writeString .= "\nFollowing problems occured during script execution:\n";
  	   	$writeString .= "-----------------------------------------------------\n";
  	   	$writeString .= "$errorString\n";
	unless ( $dryRun )
  	{
  		$writeString .= "\nTotal no. of components: $componentCount, moved/copied component: $executedComponentCount ";
  		$writeString .= "($executedArtifactCount artifacts and $executedFolderCount folders), failed: $failedExecuteComponentCount\n";
	}
  	$writeString 	 .= "Time taken: $hours hour $minutes minute $seconds second\n";
  	write_error_log($writeString);
	print "\nRefer log files for more details \nMove/Copy log      : $artifactoryLogDir$moveCopyLogFile\n"; 
	print "Error log          : $artifactoryLogDir$errorLogFile\n";
  	write_error_log("\n===========================================================================================================\n\n");
  	exit(1);
}
else 
{
	my 	$writeString  = "";
	unless ( $dryRun )
  	{
  		$writeString .= "\nTotal no. of components: $componentCount, moved/copied component: $executedComponentCount ";
  		$writeString .= "($executedArtifactCount artifacts and $executedFolderCount folders), failed: $failedExecuteComponentCount\n";
  	}
  	$writeString 	 .= "Time taken: $hours hour $minutes minute $seconds second\n";
  	write_error_log($writeString);
	print "\nRefer log files for more details \nMove/Copy log      : $artifactoryLogDir$moveCopyLogFile\n"; 
	print "Error log          : $artifactoryLogDir$errorLogFile\n";
	write_error_log("\n===========================================================================================================\n\n");
  	exit(0);
}


#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Display appropriate usage message based on the arguments : Story-48924
#
sub displayUsage
{
	my 	$argumentSelect 	= shift;
		$argumentSelect 	= 'allArguments' unless (defined $argumentSelect);           						#if maven_arguments, displays only maven usage
    my 	$writeString 		= "$$usage{'header'}\n";															#if generic_arguments, displays only generic usage
		$writeString 	   .= "\t$$usage{prefixArguments} $$usage{$argumentSelect}\n";
		$writeString  	   .= "\n\t$$usage{content}\n\n";
	foreach my $descriptionKey (sort {$a <=> $b} keys %{$$usage{description}})
	{
		my @descriptionInnerKey 		= keys %{$$usage{description}{$descriptionKey}};
		if ($$usage{$argumentSelect}  	=~ /\s$descriptionInnerKey[0]\s/)
		{
			$writeString  .= "\t$$usage{description}{$descriptionKey}{$descriptionInnerKey[0]}\n";
		}
	}
	$writeString .= "\n\t$$usage{endContent}\n\n";
	write_console($writeString);
}

#################################################################################################################
# check if source component is a version : Story-48924
#
sub versionCheck
{
	my $versionPath 			= shift;
	$versionPath				=~ /(.+)\/(.+)/;
	my ($artifactPath,$version) = ($1,$2);

    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    $cmd .= "-sS \"$server/$artifactPath/maven-metadata\.xml\"";
    my $mavenMetaXml = `$cmd`;
	#my $mavenMetaXml = `curl --noproxy \"$no_proxy\" -sS -u $userId:$password \"$server/$artifactPath/maven-metadata\.xml\"`;

  	if ($mavenMetaXml =~ /errors.+\"status\".+404/s ) 
	{
		artifactory_config::write_error_log("ERROR: Failed during version validation!\n\n");
		return(1);	
	}
	else
	{
		my $xmlRef	= XMLin($mavenMetaXml);
		
		my %versionHash = map {$_ => 1} @{$$xmlRef{versioning}{versions}{version}};
		unless ( $versionHash{$version} )
		{
			return(0);
		}
	}
	#return (0);
}

#################################################################################################################
# Remove space before and after the arguments : Story-48924
#
sub normaliseArguments
{
	my $arguments = shift;
	
	foreach my $keyArgument (keys %{$arguments})
	{
		$$arguments{$keyArgument} =~ s#^\s+##;
		$$arguments{$keyArgument} =~ s#\s+$##;
		$$arguments{$keyArgument} =~ s#\\#/#g;
		$$arguments{$keyArgument} =~ s#^/+##;
		$$arguments{$keyArgument} =~ s#/+$##;
		#print "$$arguments{$_}\n";
	}
}

#################################################################################################################
# check Arguments are passed correctly : Story-48924
#
sub argumentCheck
{	my %inputFeedRec = @_;
	if ( (!$inputFeedRec{sourceRepo}) || (!$inputFeedRec{targetRepo}) || (!$inputFeedRec{sourceComponent}) ) 
  	{
  		write_error_log("\nERROR: Arguments missing!\n");
    	($move) ? ( displayUsage('moveArguments') ) : ( displayUsage('copyArguments') );
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# extra arguments check	

  	1 while $inputFeedRec{groupId} =~ s#\/\/#\/#g;
}

#################################################################################################################
# scan arguments and assign them to global script variables  : Story-48924
# show help text if arguments are not set correctly
#
sub scanArgs
{
	my ( $h, $useproxy );
	my %inputFeed = ();

  	my $res = GetOptions (
   	'h'      		=> \$h,
   	'move'		 	=> \$move,
   	'copy'		 	=> \$copy,
   	'u=s'    		=> \$userId,
   	'p=s'    		=> \$password,
   	'f=s'    		=> \$configFile,
   	's=s'    		=> \$server,
   	'r=s'    		=> \$inputFeed{sourceRepo},
   	't=s'    		=> \$inputFeed{targetRepo},
   	'c=s'    		=> \$inputFeed{sourceComponent},
   	'd=s'    		=> \$inputFeed{targetComponent},
    'useproxy'      => \$useproxy,
   	'dryRun'    	=> \$dryRun
	) or do {
  				write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  				displayUsage('allArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
  			}; 

  	$repository_name = $inputFeed{sourceRepo};
	if(scalar @ARGV)
	{
		write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
		displayUsage('allArguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}
  	if ($h) 
  	{
  		write_error_log("\nINFO: Help message requested!\n");
   		displayUsage('allArguments');
   		write_error_log("\n===========================================================================================================\n\n");
    	exit(0);
  	}
  	unless ( $move || $copy)
  	{
  		write_error_log("\nERROR: Arguments missing!\nOperation type should be given in the arguments as (either -move for move or -copy for copy)\n");
		displayUsage('allArguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
  	}
  	if ( $move && $copy )
  	{
  		write_error_log("\nERROR: Extra argument, either move or copy operation can be selected\n");
  		displayUsage('allArguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}

	if ($configFile) 
  	{ 
  		# read infos from file
    	if ($inputFeed{sourceComponent} || $inputFeed{targetComponent} || $inputFeed{sourceRepo} || $inputFeed{targetRepo}) 
    	{
    		write_complete_log("\nWARNING: Other arguments will be ignored when using -f\n");
    	}
    	
    	# normalise path
  		$configFile = normalise_path($configFile);
  		
  		if ($configFile == 1)
  		{
  			write_error_log("\nERROR: Invalid config file: $configFile path!\n");
  			($move) ? ( displayUsage('moveArguments') ) : ( displayUsage('copyArguments') );
  			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
  		}
    	if ((! -e $configFile) || (! -f $configFile))
    	{
    		write_error_log("\nERROR: config file: $configFile not exist or not a file!\n");
			($move) ? ( displayUsage('moveArguments') ) : ( displayUsage('copyArguments') );
			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
    	}
    	open(CONFIG, "<$configFile") or do	{	write_error_log("\nMessage: $!\nERROR: Not able to open config file: $configFile!\n");
    											write_error_log("\n===========================================================================================================\n\n");
    											exit(1);
    										};
    	my @lines = <CONFIG>;
    	
    	#read each line from config_file to parse input arguments
    	foreach my $line (@lines) 
    	{
      		next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
      		chomp $line;
      		my %inputFeedCfg;
      		my $argumentCount;
      		$argumentCount = (($inputFeedCfg{sourceRepo},$inputFeedCfg{targetRepo},$inputFeedCfg{sourceComponent},$inputFeedCfg{targetComponent}) = split(/::/,$line));
      		if ($argumentCount > $configFileArgumentCount )
      		{
      			write_error_log("\nERROR: Extra arguments in config file!\n");
				($move) ? ( displayUsage('moveArguments') ) : ( displayUsage('copyArguments') );
				write_error_log("\n===========================================================================================================\n\n");
  				exit(1);
      		}
      		#print Dumper \%input_feed;
      		
      		#remove space before and after the input arguments
			normaliseArguments(\%inputFeedCfg);
			if (not defined $repository_name)
			{
				$repository_name = $inputFeedCfg{sourceRepo};
			}

      		# arguments check 
      		argumentCheck(%inputFeedCfg);
      		
      		$inputFeedCfg{targetComponent}					= $inputFeedCfg{sourceComponent} unless ( defined $inputFeedCfg{targetComponent} ) ;
      		
      		$argumentList{$inputFeedCfg{sourceComponent}}	= \%inputFeedCfg; 
    	}
    	close(CONFIG);
  	}
  	else 
  	{ 
  		#remove space before and after the input arguments
		normaliseArguments(\%inputFeed);
		
  		# arguments check for maven and generic specific     
  		argumentCheck(%inputFeed);
  		
    	$inputFeed{sourceComponent} =~ s#\\#/#g;
    	$inputFeed{targetComponent} =~ s#\\#/#g;
    	
    	$inputFeed{targetComponent} = $inputFeed{sourceComponent} unless ( defined $inputFeed{targetComponent} ) ;
		$argumentList{$inputFeed{sourceComponent}} = \%inputFeed;
  	}

  	# server, user id and password passed as arguments are given priority over .artifactory inputs
	if (! $server)
	{
        if ($useproxy)
        {
            write_complete_log("\nINFO: Proxy settings of .artifactory config file will be given priority");
        }
        ($server, $userId, $password, $no_proxy) = read_from_config();
    }
    else
    {
        if ((not $userId) && ($password)) 
        {
            write_error_log("\nERROR: User and password both have to be specified or none of them. When User and password not provided, will be read from .artifactory config file.\n");
            displayUsage('all_arguments');
            write_error_log("\n===========================================================================================================\n\n");
            exit(1);
        }
        elsif ( $userId && (not $password))
        {
            $password = get_password();
		}
        elsif ((not $userId) && ($password) || (not $userId))             
        {
            write_error_log("\nERROR: Kindly provide user id with '-u' option\n");
            write_error_log("\n===========================================================================================================\n\n");
            exit(1);
        }

        $no_proxy = ($useproxy ? "" : create_no_proxy($server));
        my $ping_status = ping_server($server, $no_proxy, $userId, $password);
        if ($ping_status)
        {
            write_error_log( "ERROR: Aborting..." );
            exit(1);
        }
	}
}
