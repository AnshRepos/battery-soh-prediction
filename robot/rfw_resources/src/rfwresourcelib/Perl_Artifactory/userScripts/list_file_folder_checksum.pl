#########################################################################################################################################
#																																		#
# FILE:          list_file_folder_checksum.pl																							#
#																																		#
# DESCRIPTION:   List file/folder along with checksum																					#
#																																		#
# USAGE:         perl list_file_folder_checksum.pl [ -h ] -r <repo> -c <component> -o <outFile> 										#
#						[ -type <artifactType>] [ -s <server>] [ -u <userId> -p <password>]												#
#																																		#
#																																		#
# COPYRIGHT:     (c) 2014 Robert Bosch GmbH																								#
# HISTORY:																																#
#																																		#
# Date         | Author                 | Modification																					#
# 01.29.2016   | Saddam Hussain A       | Initial version																				#
# 																																		#
#########################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use strict;
use Getopt::Long;
use artifactory_config;
use JSON qw( decode_json );
use Data::Dumper;
use List::Util qw( max );
use Cwd;

# Global variables
# Usage

my $usage = 
{
	'header'			=>	'Usage:',
	'prefixArguments' 	=> "perl $0",
	'allArguments' 		=> '[ -h ] -r <repo> -c <component> -o <outFile> [ -type <artifactType>] [ -s <server>] [ -u <userId> -p <password>]',
	'content' 			=> 'List files and folders.',

	'description' 		=>
		{  
			'1'  => { '-h' 			=>  '-h                       : Print this usage text.',},
    		'2'  => { '-r' 			=>  '-r    <repo>             : Artifactory source repository'},
    		'3'  => { '-c' 			=>  '-c    <component>        : Component under which listing has to be done'},
    		'4'  => { '-type'       =>  '-type <artifactType>     : Artifact type , either file or folder'},
    		'5'  => { '-o'          =>  '-o    <outFile>          : Export file name'   },
    	    '6'  => { '-s' 			=>  '-s    <server>           : Artifactory Server (optional, will be read from config file)'},
    	    '7'  => { '-u' 			=>  '-u    <userId>           : Artifactory User ID (optional, will be read from config file)'},
    	    '8'  => { '-p' 			=>  '-p    <password>         : Artifactory Password (optional, will be read from config file)'},
		},
		
    'endContent' => 'When artifact type not given all type will be displayed ( -type will also accept \'all\' as argument to display all type )
        
        When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!',
};

# arguments
my ($userId, $password, $server, $repo, $component, $outFile, $typeDecider, $errorFlag);
my $type = 'all';

# other arguments
my $localTime					= localtime;
print "TIME STAMP	: $localTime\n"; 

# Check env
if ( check_env() ) 
{
	write_error_log("\n===========================================================================================================\n\n");
	exit(0);
}

# Read arguments
scanArgs();

( $type =~ /^(folder|all)$/i) ? ( $typeDecider = 'list&deep=1&listFolders=1' ) : ( $typeDecider = 'list&deep=1&listFolders=0' ) ;

print "On server	: $server\nBase component	: $repo/$component\nOperation	: list( $type )\n\n";

# check for output file to export  	
print "INFO: Export will not be done as no output file specified!\n\n" unless ( $outFile );

# Exit if server is not pingable(It will be replaced with ping api from Artifactory version 4.2.0)
if( checkSettings($repo) )
{
	  	my 	$writeString		= "\nERROR: Repository not found or user not having read permission to ";
  			$writeString 	   .= "repository: $repo\n\n";
  			$writeString	   .= "\n===========================================================================================================\n\n";
    	print $writeString;
    	exit (1);
}

list();

if ($outFile && !$errorFlag) 
{
	print "\nSuccessfully exported output to $outFile\n";
}
print "\n===========================================================================================================\n\n";

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Display appropriate usage message based on the arguments : story-
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
		my @descriptionInnerKey = keys %{$$usage{description}{$descriptionKey}};
		if ($$usage{$argumentSelect}  	=~ /\s$descriptionInnerKey[0]\s/)
		{
			$writeString  .= "\t$$usage{description}{$descriptionKey}{$descriptionInnerKey[0]}\n";
		}
	}
	$writeString .= "\n\t$$usage{endContent}\n\n";
	print $writeString;
}





#################################################################################################################
# List files and folder
#
sub list
{
	my ( $maxHeaderLength, $maxArtifactLength ); 
	open (OUT ,'>',$outFile) or do {
  										print "\nMessage: $!\nERROR: Not able to open file: $outFile!, export will not be done.\n\n";
  										$errorFlag =1;
  									} 	if ($outFile);
  	
  	$maxHeaderLength	= max( length($server),length($repo),length($component) );
  	$maxHeaderLength += 80 ;
  	
  	if ($outFile && !$errorFlag)
  	{
  		print OUT '#'x$maxHeaderLength,"##\n#";
  		printf OUT "%*s","-$maxHeaderLength","      On server       : $server";
  		print OUT "#\n#";
  		printf OUT "%*s","-$maxHeaderLength","      Repository      : $repo";
  		print OUT "#\n#";
  		printf OUT "%*s","-$maxHeaderLength","      Base component  : /$component";
  		print OUT "#\n",'#'x$maxHeaderLength,"##\n";
  	}
	my 	$cmd  = "curl -s -X GET -u $userId:$password -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.FileList+json\" ";
		$cmd .= "\"$server/api/storage/$repo/$component?$typeDecider\" ";
	#print $cmd ;
	my $jsonOutput = `$cmd`;
	#print $jsonOutput; 
	 
	my $decodeJsonOutput = decode_json($jsonOutput);
	#print Dumper $jsonOutput;
	unless ( defined $$decodeJsonOutput{errors} )
	{
		my @artifactLengthList;
		push ( @artifactLengthList, length( $$_{uri} ) ) foreach @{$$decodeJsonOutput{files}};
		#print @artifactList;
		$maxArtifactLength = max ( @artifactLengthList ) + 2;
	
		foreach my $artifact (@{$$decodeJsonOutput{files}})
		{
			unless ($type eq 'folder')
			{
				printf "%*s : %s\n", "-$maxArtifactLength", ".$$artifact{uri}", ( "$$artifact{sha1}" || '-' );
				printf OUT "%*s : %s\n", "-$maxArtifactLength", ".$$artifact{uri}", ( "$$artifact{sha1}" || '-' );
			}
			else
			{
				if ( $$artifact{folder} eq 'true' )
				{
					printf "%*s\n", "-$maxArtifactLength", ".$$artifact{uri}";
					printf OUT "%*s\n", "-$maxArtifactLength", ".$$artifact{uri}";
				}
			}
		}
	}
	else
	{
		$errorFlag = 1;
		print "\nERROR: ${$$decodeJsonOutput{errors}}[0]{message}\n\n";
	}
}

#################################################################################################################
# check if server can be contacted and repository exist is given server
#
sub checkSettings
{
	my 	$repoToCheck		= shift;
	my 	$repoFoundFlag		= 0;
	my 	$writeString ;
  	my $getRepoCmd       	= "curl -X GET -u $userId:$password --silent \"$server/api/repositories\" ";
  	my $result    			= `$getRepoCmd`;
  	if($result =~ /errors/i)
  	{
  		$result 			=~ /.*"message"\s*:\s*\"(.*)\"/i;
  		$writeString 		= "\nMessage : $1 \n";
  		$writeString	   .= "ERROR: Could not contact artifactory server: $server for user: $userId\n\n";
    	$writeString	   .= "\n===========================================================================================================\n\n";
    	print $writeString;
    	exit(1);
  	}

  	my 	$decodeJsonResult = decode_json($result);
  	foreach (@$decodeJsonResult)
  	{
  		if ($$_{key} eq $repoToCheck)
  		{
  			$repoFoundFlag = 1;
  			last;
  		}
  	}
  	
  	return(1) unless ( $repoFoundFlag ) ;

  	return(0);
}

#################################################################################################################
# Remove space before and after the arguments : story-
#
sub normaliseArguments
{
	foreach my $argument ($repo, $component, $outFile, $type)
	{
		$argument =~ s#^\s+##;
		$argument =~ s#\s+$##;
		$argument =~ s#\\#/#g;
		$argument =~ s#^/+##;
		$argument =~ s#/+$##;
		#print "$argument\n";
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
	if ($path =~ /\.\.\./ || ( $path =~ /:/ && $path !~ /:(\\|\/)/ ) || ( $path =~ /:/ && $path =~ /(\\|\/):/ ) || $path =~ /(\\\/|\/\\)/ || $path =~ /\s+(\\|\/|\.)/ || $path =~ /(\\|\/|\.)\s+/)
	{
		return(1);
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
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly
#
sub scanArgs
{
	my $h;
  	my $res = GetOptions (
   	'h'      		=> \$h,
   	'u=s'    		=> \$userId,
   	'p=s'    		=> \$password,
   	'o=s'    		=> \$outFile,
   	's=s'    		=> \$server,
   	'r=s'    		=> \$repo,
   	'c=s'    		=> \$component,
   	'type=s'		=> \$type
	) or do {
  				print "\nERROR: Extra or unknown arguments passed, check the usage.\n";
  				displayUsage('allArguments');
				print "\n===========================================================================================================\n\n";
				exit(1);
  			}; 
  		
	if(scalar @ARGV)
	{
		print "\nERROR: Extra or unknown arguments passed, check the usage.\n";
		displayUsage('allArguments');
		print "\n===========================================================================================================\n\n";
		exit(1);
	}
  	if ($h) 
  	{
  		print "\nINFO: Help message requested!\n";
   		displayUsage('allArguments');
   		print "\n===========================================================================================================\n\n";
    	exit(0);
  	}
  	unless ( $repo || $component)
  	{
  		print "\nERROR: Repository and/or component missing!\n";
		displayUsage('allArguments');
		print "\n===========================================================================================================\n\n";
		exit(1);
  	}
  	if ( (not $userId) && ($password) || (not $password) && ($userId)) 
  	{
  		print "\nERROR: User and password both have to be specified or none of them. When User and password not provided, will be read from .artifactory config file.\n";
		displayUsage('allArguments');
		print "\n===========================================================================================================\n\n";
    	exit(1);
  	}

  	# normalise path  	
  	if ( $outFile && ( $outFile = normalisePath($outFile) ) && $outFile == 1)
  	{
  		print "\nERROR: Invalid output file!\n";
		displayUsage('allArguments');
		print "\n===========================================================================================================\n\n";
    	exit(1);
  	}

  	#remove space before and after the input arguments
	normaliseArguments();
	  	
  	$type = lc $type;      # convert type value to lowercase
  	
  	if ( $type && $type !~ /^(folder|file|all)$/ )
  	{
  		print "\nERROR: Invalid artifact type, type should be all or folder or file!\n";
		displayUsage('allArguments');
		print "\n===========================================================================================================\n\n";
    	exit(1);
  	}
			
  	# read server from standard config file
  	my ( $cfgServer, $cfgUserId, $cfgPassword ,$result);

  	# server, user id and password passed as arguments are given priority over .artifactory inputs
  	if ((not $server) || (not $userId))
  	{
  		# read server from .artifactory config file

  		($cfgServer,$cfgUserId,$cfgPassword,$result) = read_from_config();
  		if ($result eq "1") {print "\nERROR: No script execution because of errors, no erro code on request -> exit with status 0\n";exit(0);}    # requested not to exit with errors in order to continue calling scripts
  		if ($result eq "2") {print "\nERROR: Script $0 aborted, exit with status 1\n";exit(1);}    # exit with error
  		if ($result eq "3") {print "\n===========================================================================================================\n\n";exit(1);}  # exit when .artifactory file not exist
  	}	
  	
  	# overwrite with argument settings if available
  	$server   = $cfgServer if ($server eq "");
  	if ($userId eq "") 
  	{
  		$userId   		= $cfgUserId;
  		$password      	= $cfgPassword;
  	}
  	else
  	{
  		my $fetchEncryptePasswordCmd = "";
  		$fetchEncryptePasswordCmd =  "curl -sS -X GET -u $userId:$password \"$server/api/security/encryptedPassword\"" if ($^O =~ /mswin/i || $^O =~ /cygwin/i) ;
  	  	$fetchEncryptePasswordCmd =  "curl -sS -X GET -u \'$userId:$password\' \"$server/api/security/encryptedPassword\"" if ($^O =~ /linux/i);
      	$password = `$fetchEncryptePasswordCmd`;
      	if ($password =~ /errors/) 
      	{
        	print "\nERROR: Unknown problems in interacting with artifactory server to get encrypted password, abort...\n";
        	print "\n===========================================================================================================\n\n";
        	exit(1);
      	}
  	}
}