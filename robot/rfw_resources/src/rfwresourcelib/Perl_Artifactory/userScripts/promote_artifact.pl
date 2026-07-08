#############################################################################################################################################################
#																																							#
# FILE			:   promote_artifact.pl																														#
#																																							#
# DESCRIPTION	:	Promote artifact version based on Retention class property.																				#
#																																							#
# USAGE			:   perl promote_artfiact.pl [ -h ] ( -m | -d ) -f <configFile> | -r <srcRepo> -t <targetRepo> ( -c <component> | 							#
#					( -g <groupId> -a <artifactId> -v <versionId>)) -prjUsed <projectUsed> -retC <retC> [ -s <server> -u <userId> -p <password>             #
#                   -useproxy ]                                                                                                                             #
#																																							#
# ARGUMENTS		:   see Usage																																#
#																																							#
# COPYRIGHT		:   (c) 2014 Robert Bosch GmbH																												#
# HISTORY		:																																			#
#																																							#
# Date         	| Author                		| 	Modification																							#
# 05.11.2015   	| Saddam hussain A (RBEI/ECA2)  | 	Initial version : Story 44165																			#
# 18.12.2015  	| Saddam hussain A (RBEI/ECA2)	| 	JSON decoder used to parse json output from artifactory rest api : story-45582							#
#										  			Path normalisation : story-45582																		#
#										  			Maven and generic repository handled : story-45582														#
#										  			Arguments check for maven and generic repository layout added : story-45582								#
#										  			Logger file adaption, Set property function to set property for promoted artifact : story-47335			#
#										  			Input parameter modified to read project name and retention class to set for the  						#	
#													promoted artifact: story-47335																			#
# 01.01.2016   	| Saddam hussain A (RBEI/ECA2)	| 	Check settings function has been added : story-47335													#
#										  			Fix to check for input config file : story-47335														#
# 01.03.2016	| Saddam hussain A (RBEI/ECA2)	| 	Adapt to new config file ( check settings, normalise path function)	: story-52828						#
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		| 	Modified code to handle empty line with spaces in config file					 						#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | 	Made modifications to set property based on Artifactory version and added latest script version check 	#
#													functionality: story-165111																				#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		| 	Added feature to stop execution of older scripts: story-185699											#
# 20.03.2019	| Sounak Patra (RBEI/ECQ2)		|   Added noproxy option in curl                                                                            #
#																																							#
#############################################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use Getopt::Long;
use Data::Dumper;
use Cwd;
use JSON qw( decode_json );

# Usage
my $usage = 
{
	'header'			=>	'Usage:',
	'prefixArguments' 	=> "perl $0",
	'allArguments' 		=> '[ -h ] ( -m | -d ) -f <configFile> | -r <srcRepo> -t <targetRepo> ( -c <component> |( -g <groupId> -a <artifactId> -v <versionId> )) -prjUsed <projectUsed> -retC <retC> [ -s <server> -u <userId> -p <password> -useproxy ]',
	'mavenArguments'	=> ' -m -f <configFile> | -r <srcRepo> -t <targetRepo> -g <groupId> -a <artifactId> -v <versionId> -prjUsed <projectUsed> -retC <retC> [ -s <server> -u <userId> -p <password> -useproxy ]',
	'genericArguments' 	=> ' -d -f <configFile> | -r <srcRepo> -t <targetRepo> -c <component> -prjUsed <projectUsed> -retC <retC> [ -s <server> -u <userId> -p <password> -useproxy ]',
	'content' 			=> 'Recursively promote content.',

	'description' 		=>
		{  
			'1'  => { '-h' 			=>  '-h                    : Print this usage text.',},
    		'2'  => { '-m' 			=>  '-m <maven>            : For maven repository layout',},
    		'3'  => { '-d' 			=>  '-d <generic>          : For generic repository layout'},
    		'4'  => { '-r' 			=>  '-r <srcRepo>          : Artifactory source repository'},
    		'5'  => { '-t'          =>  '-t <targetRepo        : Artifactory target repository'},
    		'6'  => { '-f' 			=>  '-f <configFile>       : Path to config file'},
    		'7'  => { '-c' 			=>  '-c <component>        : Component (relative path inside repository)'},
    		'8'  => { '-g' 		    =>  '-g <groupId>          : GroupId, applicable for maven layout, use together with -a & -v'},
    		'9'  => { '-a' 		    =>  '-a <artifactId>       : ArtifactId, applicable for maven layout, use together with -g & -v'},
    	   '10'  => { '-v' 		    =>  '-v <versionId>        : VersionId, applicable for maven layout, use together with -g & -a'},
    	   '11'  => { '-prjUsed' 	=>  '-prjUsed <projectUsed>: Project using artifact (comma separated list)'},
    	   '12'  => { '-retC' 		=>  '-retC <retC>          : Retention class (atleast one retention value i.e., 4/3/2/1/0)'},
    	   '13'  => { '-s' 			=>  '-s <server>           : Artifactory Server (optional, will be read from config file)'},
    	   '14'  => { '-u' 			=>  '-u <userId>           : Artifactory User ID (optional, will be read from config file)'},
    	   '15'  => { '-p' 			=>  '-p <password>         : Artifactory Password (optional, will be read from config file)'},
           '17'  => { '-useproxy' =>  '-useproxy             : Uses current proxy settings (optional, will override config file)'}
		},
    'endContent' => 'Other arguments will be ignored when using -f
    	Format of <config_file>:
				# used with comments
				# one line per promotion; items seperated by two colon; all arguments are mandatory
				sourceRepository::targetRepository::component::prjUsed::retC 					if generic repository
				sourceRepository::targetRepository::group_id::artifact_id::version::prjUsed::retC 	if maven repository
       	
				When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!',
};

# current date
my ($day, $mon, $year)  = (localtime)[3,4,5];
my $cur_date            = sprintf "%04d-%02d-%02d",($year+1900),($mon+1),$day;

# arguments
my ( $server, $userId, $password, $repository_name, $no_proxy );
my $maven			= "";
my $generic			= "";
my $configFile		= "";

#derived from arguments
my %argumentList				= ();
# other vars	
my %config						= ();
my $startTime					= time();
my $endTime						= 0;
my $componentToPromoteCount		= 0;
my $promotedComponentCount		= 0;
my $promotedArtifactCount		= 0;
my $promotedFolderCount 		= 0;
my $errorPromoteComponentCount	= 0;
my $errorString 				= "";
my $mavenArgumentCount			= 7;
my $genericArgumentCount		= 5;

my $promoteLogFile       		= 'promote.log' ;
my $errorLogFile		   		= 'promote_error.log';
my $auto_answer   				= $ENV{_SET_ENV_AUTO_ANSWER};
   
# Create log file
my $artifactoryLogDir = create_log_file( $promoteLogFile,$errorLogFile );
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

#print Dumper \%argumentList;
$componentToPromoteCount = keys %argumentList;
write_error_log("On Server\t: $server\nOpertation 	: Promote\n\n");

NEXT: foreach my $targetArtifact (keys %argumentList)
{
	if (check_settings( $server, $userId, $password, $argumentList{$targetArtifact}{srcRepo}, $no_proxy ))									# source repository existence check
	{
		my	$writeString		= "\nERROR: Source repository not found or user not having read permission to ";
  			$writeString 	   .= "repository: $argumentList{$targetArtifact}{srcRepo} in artifactory server: $server\n\n";
    	write_error_log($writeString);
    	$errorString           .= $writeString;
		next NEXT; 
	}													
	if (check_settings( $server, $userId, $password, $argumentList{$targetArtifact}{srcRepo}, $no_proxy ))									# target repository existence check
	{
		my	$writeString		= "\nERROR: Target repository not found or user not having read permission to ";
  			$writeString 	   .= "repository: $argumentList{$targetArtifact}{srcRepo} in artifactory server: $server\n\n";
    	write_error_log($writeString);
    	$errorString           .= $writeString;
		next NEXT; 
	}

	#promoting artifacts
    my $moveCmd = set_curl_command($no_proxy, $userId, $password, 0);
	$moveCmd .= "-s -X POST -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.CopyOrMoveResult+json\" ";
	$moveCmd .= "\"$server/api/move/$argumentList{$targetArtifact}{srcRepo}/$targetArtifact?to=/$argumentList{$targetArtifact}{targetRepo}/$targetArtifact\" ";
	my $moveOutput = `$moveCmd`;
	chomp $moveOutput;

	my $decodedMoveOutput = decode_json($moveOutput);
	# Example output for moving artifact
	#{
  	#	"messages" : [ {
	#	"level" : "INFO", or "ERROR"
    # 	"message" : "moving test-release:g/a/1.0 to test-repo:g/a/1.0 completed successfully, 20 artifacts and 9 folders were moved"
  	#	} ]
	#}
	if ($decodedMoveOutput->{messages}[0]{level} =~ /ERROR/i)
	{ 
		#write_complete_log("- PROMOTION FAILED\n");
		write_error_log("$argumentList{$targetArtifact}{srcRepo}/$targetArtifact==>$argumentList{$targetArtifact}{targetRepo}/$targetArtifact - PROMOTION FAILED\n");
		$errorString .= "ERROR: Failed to promote Artifact: $targetArtifact - Message: $decodedMoveOutput->{messages}[0]{message}\n";
		$errorPromoteComponentCount++;
	}
	else
	{
		write_complete_log("$argumentList{$targetArtifact}{srcRepo}/$targetArtifact==>$argumentList{$targetArtifact}{targetRepo}/$targetArtifact - PROMOTION OK -");
		#print " $decodedMoveOutput->{messages}[0]{message}\n";
		my $stringToParse = $decodedMoveOutput->{messages}[0]{message};
		$stringToParse =~ /\S+,\s*(\d+)\s*artifacts\s*and\s*(\d+)\s*folders/;
		$promotedArtifactCount += $1;
		$promotedFolderCount   += $2;
		$promotedComponentCount++;
		setProps($targetArtifact);
	}
}

# Calculate time to complete promotion
$endTime 		= time();
my $duration 	= $endTime - $startTime;
my $minutes 	= int ( ( $duration / 60 ) % 60 );
my $seconds 	= $duration % 60;
my $hours 		= int( ( $duration /60) / 60 );
# Check for intermediate errors and exit
if ($errorString ne "") 
{
	my $writeString  = "";
  	   $writeString .= "\nFollowing problems occured during script execution:\n";
  	   $writeString .= "-----------------------------------------------------\n";
  	   $writeString .= "$errorString\n";
  	   $writeString .= "\nTotal no. of components: $componentToPromoteCount, promoted component: $promotedComponentCount ($promotedArtifactCount files and $promotedFolderCount folders), failed: $errorPromoteComponentCount\n";
  	   $writeString .= "Time taken: $hours hour $minutes minute $seconds second\n";
  	
  	write_error_log($writeString);
	print "\nRefer log files for more details \nPromote log      : $artifactoryLogDir$promoteLogFile\n"; 
	print "Error log        : $artifactoryLogDir$errorLogFile\n";
  	write_error_log("\n===========================================================================================================\n\n");
  	exit(1);
}
else 
{
	my $writeString .= "\nTotal no. of components: $componentToPromoteCount, promoted component: $promotedComponentCount ($promotedArtifactCount files and $promotedFolderCount folders), failed: $errorPromoteComponentCount\n";
  	   $writeString .= "Time taken: $hours hour $minutes minute $seconds second\n";
  	   
	write_error_log($writeString);
	print "\nRefer log files for more details \nPromote log      : $artifactoryLogDir$promoteLogFile\n"; 
	print "Error log        : $artifactoryLogDir$errorLogFile\n";
	write_error_log("\n===========================================================================================================\n\n");
  	exit(0);
}
#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Display appropriate usage message based on the arguments : story-47335
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
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly
#
sub scanArgs
{
	my ($h, $srcArtifact);
	my %inputFeed = ();

  	my $res = GetOptions (
   	'h'      	=> \$h,
   	'm'		 	=> \$maven,
   	'd'		 	=> \$generic,
   	'u=s'    	=> \$userId,
   	'p=s'    	=> \$password,
   	'f=s'    	=> \$configFile,
   	's=s'    	=> \$server,
   	'r=s'    	=> \$inputFeed{srcRepo},
   	't=s'    	=> \$inputFeed{targetRepo},
   	'c=s'    	=> \$inputFeed{component},
   	'g=s'    	=> \$inputFeed{groupId},
   	'a=s'    	=> \$inputFeed{artifactId},
   	'v=s'    	=> \$inputFeed{version},
   	'prjUsed=s'	=> \$inputFeed{prjUsed},
   	'retC=i'   	=> \$inputFeed{retC},
    'useproxy'    => \$useproxy,
  	) or do {
  				write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  				displayUsage('allArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
  			}; 
  		
	$repository_name = $inputFeed{srcRepo};
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
  	unless ( $maven || $generic)
  	{
  		write_error_log("\nERROR: Arguments missing!\nRepository type should be given in the arguments as (either -m for maven or -d for generic)\n");
		displayUsage('allArguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
  	}
  	if ($maven && $generic)
  	{
  		write_error_log("\nERROR: Extra argument, either generic or maven option can be selected\n");
  		displayUsage('allArguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}

	if ($configFile) 
  	{ # read infos from file
    	if ($inputFeed{component} || $inputFeed{groupId} || $inputFeed{artifactId} || $inputFeed{version} || $inputFeed{srcRepo} || $inputFeed{targetRepo}) 
    	{
    		write_complete_log("\nWARNING: Other arguments will be ignored when using -f\n");
    	}
    	# normalise path
  		$configFile = normalise_path($configFile);
  		if ($configFile == 1)
  		{
  			write_error_log("\nERROR: Invalid config file: $configFile path!\n");
			displayUsage('mavenArguments') 	if ($maven);
			displayUsage('genericArguments') 	if ($generic);
  			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
  		}
    	if ((! -e $configFile) || (! -f $configFile))
    	{
    		write_error_log("\nERROR: config file: $configFile not exist or not a file!\n");
			displayUsage('mavenArguments') 	if ($maven);
			displayUsage('genericArguments') 	if ($generic);
			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
    	}
    	open(CONFIG, "<$configFile") or do	{	write_error_log("\nMessage: $!\nERROR: Not able to open config file: $configFile!\n");
    											write_error_log("\n===========================================================================================================\n\n");
    											exit(1);
    										};
    	my @lines = <CONFIG>;
    	close(CONFIG);
    	
    	if ($maven)
    	{
    		# read each line from config_file to parse input arguments
    		foreach my $line (@lines) 
    		{
      			next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
      			chomp $line;
      			my %inputFeedCfg;
      			my $argumentCount;
      			$argumentCount = (($inputFeedCfg{srcRepo},$inputFeedCfg{targetRepo},$inputFeedCfg{groupId},$inputFeedCfg{artifactId},$inputFeedCfg{version},$inputFeedCfg{prjUsed},$inputFeedCfg{retC}) = split(/::/,$line));
      			if ( $argumentCount > $mavenArgumentCount )
      			{
      				write_error_log("\nERROR: Extra arguments in config file!\n");
					displayUsage('mavenArguments');
					write_error_log("\n===========================================================================================================\n\n");
  					exit(1);
      			}
      			# remove space before and after the input arguments
				normaliseArguments(\%inputFeedCfg);
				if (not defined $repository_name)
				{
					$repository_name = $inputFeedCfg{srcRepo};
				}
				
      			# maven arguments check 
      			mavenArgumentCheck(%inputFeedCfg);
      			$srcArtifact 				= "$inputFeedCfg{groupId}/$inputFeedCfg{artifactId}/$inputFeedCfg{version}";
    			$srcArtifact       			=~ s#\\#/#g;
  				$argumentList{$srcArtifact} = \%inputFeedCfg;
    		}
    	}
    	else
    	{
    		foreach my $line (@lines) 
    		{
      			next if ($line =~ /#/ || $line =~ /^$/); 	# ignore comments and empty lines
      			chomp $line;
      			my %inputFeedCfg;
      			my $argumentCount;
      			$argumentCount = (($inputFeedCfg{srcRepo},$inputFeedCfg{targetRepo},$inputFeedCfg{component},$inputFeedCfg{prjUsed},$inputFeedCfg{retC}) = split(/::/,$line));
      			if ( $argumentCount > $genericArgumentCount )
      			{
      				write_error_log("\nERROR: Extra arguments in config file!\n");
					displayUsage('genericArguments');
					write_error_log("\n===========================================================================================================\n\n");
  					exit(1);
      			}
      			
      			# remove space before and after the input arguments
				normaliseArguments(\%inputFeedCfg);
				if (not defined $repository_name)
				{
					$repository_name = $inputFeedCfg{srcRepo};
				}				

      			# generic arguments check 
    			genericArgumentCheck(%inputFeedCfg);
    			$srcArtifact				= $inputFeedCfg{component};
    			$srcArtifact       			=~ s#\\#/#g;
  				$argumentList{$srcArtifact} = \%inputFeedCfg;
    		}
    	}
    	close(CONFIG);
  	}
  	else 
  	{ 
  		#remove space before and after the input arguments
		normaliseArguments(\%inputFeed);
		
  		# arguments check for maven and generic specific     
  		if ($maven)
  		{
  			mavenArgumentCheck(%inputFeed);
  			$srcArtifact = "$inputFeed{groupId}/$inputFeed{artifactId}/$inputFeed{version}";
  		}
  		else
  		{	
  			genericArgumentCheck(%inputFeed); 
  			$srcArtifact = "$inputFeed{component}";
  		}	
  		
    	$srcArtifact       =~ s#\\#/#g;
		$argumentList{$srcArtifact} = \%inputFeed;
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
#################################################################################################################
# check maven arguments are passed correctly : story-45582
#
sub mavenArgumentCheck
{	my %inputFeedRec = @_;
	if ((!$inputFeedRec{srcRepo}) || (!$inputFeedRec{targetRepo}) || (!$inputFeedRec{groupId}) || (!$inputFeedRec{artifactId}) || (!$inputFeedRec{version}) || (!$inputFeedRec{prjUsed}) || !(defined $inputFeedRec{retC})) 
  	{
  		write_error_log("\nERROR: Arguments missing!\n");
    	displayUsage('mavenArguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# extra arguments check	
  	if ($inputFeedRec{component}) 
  	{
  		write_error_log("\nERROR: Extra arguments!\n");
		displayUsage('mavenArguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	# artifact id and version correctness check 
  	if ( ($inputFeedRec{artifactId} =~ /(\\|\/)/) || ($inputFeedRec{version} =~ /(\\|\/)/) )
  	{
  		write_error_log("\nERROR: Invalid Artifact id or Version!\n");
		displayUsage('mavenArguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	if ($inputFeedRec{retC} !~ /^\d/ || $inputFeedRec{retC} !~ /\d$/ || $inputFeedRec{retC} =~ /[^,01234]/)
  	{
  		write_error_log("\nERROR: Invalid retC value (should be within 0 to 4)!\n");
		displayUsage('mavenArguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}

  	1 while $inputFeedRec{groupId} =~ s#^(\\|\/)##g;
  	1 while $inputFeedRec{groupId} =~ s#(\\|\/)$##g;
  	1 while $inputFeedRec{groupId} =~ s#\\\\|\/\/#\/#g;
}
#################################################################################################################
# check genric arguments are passed correctly : story-45582
#
sub genericArgumentCheck
{
	my %inputFeedRec = @_;
	#print Dumper \%inputFeedRec;
  	if ((!$inputFeedRec{srcRepo}) || (!$inputFeedRec{targetRepo}) || (!$inputFeedRec{component}) || (!$inputFeedRec{prjUsed}) || !(defined $inputFeedRec{retC})) 
  	{
    	write_error_log("\nERROR: Arguments missing!\n");
    	displayUsage('genericArguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	if ($inputFeedRec{groupId} || $inputFeedRec{artifactId} || $inputFeedRec{version}) 
  	{
  		write_error_log("\nERROR: Extra arguments!\n");
  		displayUsage('genericArguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	if ($inputFeedRec{retC} !~ /^\d/ || $inputFeedRec{retC} !~ /\d$/ || $inputFeedRec{retC} =~ /[^,01234]/)
  	{
  		write_error_log("\nERROR: Invalid retC value (should be within 0 to 4)!\n");
		displayUsage('genericArguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}

  	1 while $inputFeedRec{component} =~ s#^(\\|\/)##g;
  	1 while $inputFeedRec{component} =~ s#(\\|\/)$##g;
  	1 while $inputFeedRec{component} =~ s#\\\\|\/\/#\/#g;
}
#################################################################################################################
# Remove space before and after the arguments : story-45582
#
sub normaliseArguments
{
	my $arguments = shift;
	
	foreach my $keyArgument (keys %{$arguments})
	{
		$$arguments{$keyArgument} =~ s#^\s+##;
		$$arguments{$keyArgument} =~ s#\s+$##;
		#print "$$arguments{$_}\n";
	}
}
#################################################################################################################
# Normalise path from unix, window path and also from relative, canonical path (remove unnecessary slashes also) : story-45582
#
sub normalisePath
{
	my $path 				= shift;
	#my $rel_to_abs_flag 	= 1;
	my $cwd 				= getcwd;
	if ($path =~ /\.\.\./ || ( $path =~ /:/ && $path !~ /:(\\|\/)/ ) || $path =~ /(\\\/|\/\\)/ || $path =~ /\s+(\\|\/|\.)/ || $path =~ /(\\|\/|\.)\s+/)
	{
		write_error_log("\nERROR: Invalid config file path\n");
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}
	if (($path =~ /^\.$/) || ($path =~ /^\.(\\|\/)$/))
	{
		$path 				= getcwd();
	}
	if (($path =~ /^\.\.$/) || ($path =~ /^\.\.(\\|\/)$/))
	{
		$path 				= getcwd();
		$path 				= dirname($path);
	}
	if ($^O =~ /linux/i || $^O =~ /cygwin/i)
  	{
  	    1 while $path		=~ s#\\#/#g ;
  		$path				=~ s#\/+$## if ($path !~ /^\w:\/$/  && $path !~ /^\/$/);				#remove extra slash at last
  	}
  	if ($^O =~ /mswin/i)
  	{ 
  		
  		($path !~ /^(\\|\/)+$/) ? $path	=~ s#^\\\\#\#\!\#\!\## : $path =~ s#^(\\|\/)+$#/#;
  	    1 while $path		=~ s#\\#/#g ;
  				$path		=~ s#\#\!\#\!\##\\\\#;
  				$path		=~ s#\/+$## if ($path !~ /^\w:\/$/  && $path !~ /^\/$/);				#remove extra slash at last
  	}
	LOOP: while(1)
	{
  		1 while 		 $path 	=~ s#//#/#g;
  		1 while 		 $path 	=~ s#^(\/|\w:)\/?\.\/#$1/#;
		1 while 		 $path 	=~ s#^(\/|\w:)\/?\.\.\/#$1/#;
		1 while 		 $path 	=~ s#//#/#g;
		
		if ($path =~ /^(\/|\w:\/|\\\\)/)
		{
			#$path =~ s#
			next LOOP if $path 	=~ s#\/\.\/#/#;
			next LOOP if $path 	=~ s#/([^/]*)\/\.\.\/#/#;
			1 while 	 $path	=~ s#//#/#g;
		}
		else
		{
						 $path 	= "$cwd/$path";
			next LOOP if $path 	=~ s#\/\.\/#/#;
			next LOOP if $path 	=~ s#/([^/]*)\/\.\.\/#/#;
			1 while 	 $path 	=~ s#//#/#g;
		}
		next LOOP if $path 		=~ s#\/\.$#/#;
		next LOOP if $path 		=~ s#/([^/]*)\/\.\.$#/#;
					 $path		=~ s#\/+$## if ($path !~ /^\w:\/$/ && $path !~ /^\/$/);
		last;
	}
	return ($path);
}
#################################################################################################################
# set properties on version directory : story-47335
#
sub setProps
{
	my ($targetArtifactRec) = @_;
	my $artifactory_version = get_artifactory_version($server, $no_proxy);

   	write_complete_log(" properties retention.RetDate=$cur_date|retention.PrjUsed=$argumentList{$targetArtifactRec}{prjUsed}|retention.RetC=$argumentList{$targetArtifactRec}{retC}&recursive=0 set -");
	
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
  	$cmd .= "-sS -X PUT $server/api/storage/$argumentList{$targetArtifactRec}{targetRepo}/$targetArtifactRec?properties=";

  	if ($artifactory_version >= 5.0)
  	{
  		$cmd .= "\"retention.RetDate=$cur_date;retention.PrjUsed=$argumentList{$targetArtifactRec}{prjUsed};retention.RetC=$argumentList{$targetArtifactRec}{retC}&recursive=0\"";
  	}
  	else
  	{
  		$cmd .= "\"retention.RetDate=$cur_date|retention.PrjUsed=$argumentList{$targetArtifactRec}{prjUsed}|retention.RetC=$argumentList{$targetArtifactRec}{retC}&recursive=0\"";
  	}

  	my $output = `$cmd`;
  	if ($output)
  	{
  		my $decodeJson = decode_json($output) ;
  		if (defined $decodeJson->{'errors'} )
  		{
  			write_complete_log("$$decodeJson{errors}[0]{status} - ERROR\n\n");
  			$errorString .= "Error setting artifact: $targetArtifactRec properties - Message: $$decodeJson{errors}[0]{message}\n";
  		}
  	}
  	else 
  	{
    	write_complete_log(" Ok\n");
  	}
}
