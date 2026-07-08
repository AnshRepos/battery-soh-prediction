#############################################################################################################################################
#                                                                                                                                           #
# FILE			:   deploy_file.pl																											#
#                                                                                                                                           #
# DESCRIPTION	:   Deploy/Upload a single file to an artifactory repository																#
#                                                                                                                                           #
# USAGE			:   deploy_file.pl [-h] ( ( -r <repo> -i <fileArtifact> -c <targetFolder> ) | -f <configFile> ) 							#
#										[ -verbose ] [ -s <server> -u <userId> -p <password> -useproxy]                                     #
#                                                                                                                                           #
# ARGUMENTS		:   See usage																												#
#                                                                                                                                           #
# COPYRIGHT		:   (c) 2014 Robert Bosch GmbH																								#
# HISTORY		:																															#
#                                                                                                                                           #
# Date         	| Author                 		| Modification																				#
# 20.10.2014   	| M.Schoenfelder (ext)   		| Initial version																			#
# 22.06.2015   	| M.Schoenfelder (ext)   		| adapt to new config file																	#
# 14.09.2015   	| M.Schoenfelder (ext)   		| do not allow spaces for target folder and source file										#
# 01.03.2016	| Saddam hussain A 	(RBEI/ECA2)	| Adapt to new config file ( check settings, normalise path function),						# 
#												  multi file upload	: story-52826															#
# 15.06.2016 	| Saddam hussain A  (RBEI/ECA2)	| Added functionality to process Ant wild cards character to upload							# 
#                                                 multiple files : story-62230                                                              #
#												  Added Folder validation before uploading to it : story-63369							  	#
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled windows based execution: feature-76330                                            #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled verbose mode and progress bar: feature- 76327                                     #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled mac based execution: feature- 76330                                               #
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		| Modified code to handle empty line with spaces in config file					 			#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | Made modifications to check latest script version: story-165111							#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		| Added feature to stop execution of older scripts: story-185699							#
# 31.05.2018	| Sounak Patra (RBEI/ECQ2)		| Fixed wrong md5 checksum generation in Mac OS: story-274782								#
# 19.03.2019	| Sounak Patra (RBEI/ECQ2)		| Added noproxy option in curl                                                              #
#                                                                                                                                           #
#############################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use Getopt::Long;
use Text::Glob qw( glob_to_regex );

# Usage
my $usage = "
Usage:
  perl $0 [-h] ( ( -r <repo> -i <fileArtifact> -c <targetFolder> ) | -f <configFile> ) [ -verbose ] [ -s <server> -u <userId> -p <password> -useproxy ]

  Upload a single file from artifactory.

       -h                    : Print helper message
       -f     <configFile>   : Configuration file with all argument information
       -i     <fileArtifact> : File to be uploaded, cannot be used with -f
       -c     <targetFolder> : Target folder in repository, cannot be used with -f
       -r     <repo>         : Artifactory repository, cannot be used with -f
       -force                : Force upload (optional, it will enable user to overwrite existing file inside repository.
                                             User should have DELETE permission)
       -verbose              : Verbose mode
       -s     <server>       : Artifactory Server (optional, will override config file)
       -u     <userId>       : Artifactory User ID (optional, will override config file)
       -p     <password>     : Artifactory Password (optional, will override config file)
       -useproxy             : Uses current proxy settings (optional, will override config file)
       
  Format of <configFile>:
	# used with comments
	# one line per upload; items seperated by two colon; all arguments are mandatory
	Repository::targetFolder::fileArtifact
       	
  When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!

  Wildcards:
    Supports Ant wild cards '?' matches single and '*' matches zero or more characters, using other wild card characters will give unreliable results.    
    Supports Alternation( example.{foo,bar,baz} matches example.foo, example.bar, and example.baz )
    Supports Character sets/ranges( example.[ch] matches example.c and example.h, demo.[a-c][c-e] matches demo.ac, demo.bd, and demo.ce )
\n";

# arguments
my ( $server, $userId, $password, $verboseMode, $repository_name, $no_proxy );
my ( @argumentList, $force );

# other arguments
#my @files						= ();
my ( $artifactToUpload, $uploadedArtifact, $overwrittenArtifact, $failedArtifact) = ( 0, 0, 0, 0 );
my $autoAnswer   				= $ENV{_SET_ENV_AUTO_ANSWER};
my $configFileArgumentsCount 	= 3;					# Repository::targetFolder::fileArtifact
my $errorString 				= "";
my $uploadLogFile       		= 'upload.log';
my $errorLogFile		   		= 'upload_error.log';
my $startTime					= time();
my $endTime						= 0;
my $devNul 						= "/dev/null";
   
# Create log file
my $artifactoryLogDir = create_log_file( $uploadLogFile,$errorLogFile );
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

if ( $force )
{
	write_error_log("On Server\t\t: $server\nOperation\t\t: Upload single file( force )\n", $verboseMode);
}
else
{
	write_error_log("On Server\t\t: $server\nOperation\t\t: Upload single file\n", $verboseMode);
}

#$artifactToUpload = scalar @argumentList;
print "On Server\t: $server\n" if (not $verboseMode);

CONFIG: 
	my $versionCount = 0;
	print "\n";
	foreach my $inputFeedHref (@argumentList) 
	{
		$versionCount ++;
		# Exit if server is not pingable(It will be replaced with ping api from Artifactory version 4.2.0)
		if(check_settings($server, $userId, $password, $$inputFeedHref{'repo'}, $no_proxy)) 					# source repository existence check
		{
			my 	$writeString			= "\nERROR: Target repository not found or user not having read permission to ";
				$writeString 	       .= "repository: $$inputFeedHref{'repo'} in artifactory server: $server\n\n";
		   	write_error_log($writeString);
		   	$errorString           .= $writeString;
		   	next CONFIG;
		}
  		
  	   	my $writeString    = "\nProcessing upload to $$inputFeedHref{'repo'}/$$inputFeedHref{'targetFolder'} from $$inputFeedHref{'fileArtifact'}\n\n";
		write_error_log($writeString, $verboseMode); 
		
		# component existence check
		next CONFIG if ( my $error = folderValidationCheck( %{$inputFeedHref}) );
  		
  		my @filesToUpload	= ();			# reset file list for every upload from config file
  		
  		if ( basename( $$inputFeedHref{'fileArtifact'} ) =~ /[*?{[]/ )        # call for search file function only if the given file has wildcard characters.
  		{
  			@filesToUpload = searchFile( %{$inputFeedHref} );
  			next CONFIG if ( scalar @filesToUpload == 0 );
  		}
  		else
  		{
  			push( @filesToUpload, $$inputFeedHref{'fileArtifact'} )
  		}
  		
  		# total artifacts to upload count
  		$artifactToUpload = scalar @filesToUpload;
  		
  		# upload files 
  		upload( $inputFeedHref, \@filesToUpload, $versionCount, scalar @argumentList );
	}
	print "\n";

# Calculate time to complete download
$endTime 		= time();
my $duration 	= $endTime - $startTime;
my $minutes 	= int ( ( $duration / 60 ) % 60 );
my $seconds 	= $duration % 60;
my $hours 		= int( ( $duration /60) / 60 );

# Check for intermediate errors and exit
if ($errorString ne "") 
{
	my $writeString = "";
  	   $writeString .= "\nFollowing problems occured during script execution:\n";
  	   $writeString .= "-----------------------------------------------------\n";
  	   $writeString .= "$errorString\n\n";
  	write_error_log($writeString);
  	write_error_log("\nTotal no. of files: $artifactToUpload, uploaded: $uploadedArtifact, failed: $failedArtifact\n");
  	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nUpload log       : $artifactoryLogDir$uploadLogFile\n"; 
	print "Error log        : $artifactoryLogDir$errorLogFile\n";
  	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(1);
}
else 
{
	write_error_log("\nTotal no. of files: $artifactToUpload, uploaded: $uploadedArtifact, failed: $failedArtifact\n");
	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nUpload log       : $artifactoryLogDir$uploadLogFile\n"; 
	print "Error log        : $artifactoryLogDir$errorLogFile\n";
	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(0);
}

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# deploy file : story-52826
sub upload
{
	my ($inputFeedHref, $filesToUploadAref, $versionCount, $totalNoOfVersions) 	= @_;
	my $fileCount				= scalar @{$filesToUploadAref};
	my $fileUploadProgress	= 0;

	write_complete_log("Uploading $fileCount files...\n", $verboseMode);
	my ($md5Value, $sha1Value);
  	my $def_percentage_counter = 0;
  	   $def_percentage_counter = (100 / scalar @{$filesToUploadAref}) if (scalar @{$filesToUploadAref});
	
	for my $file ( @{$filesToUploadAref} )
	{
		$fileUploadProgress++;
		$file 			=~ s#^\\\\#\\\\\\\\# if ($^O =~ /mswin/i);             	# incase of UNC path replace \\ with \\\\  
   	    	
	    # generate checksums
    	$md5Value  = get_hash_value('MD5', $file);
    	$sha1Value = get_hash_value('SHA1', $file);    	
    	
     	if ($file 	=~ /_content.sha1/i or ($file =~ /\.pom$/i))
    	{
    		write_complete_log("\nSkipping $file\n", $verboseMode);
    		next;
    	}
	    		
		my $depolyProgress	= "($fileUploadProgress\/$fileCount)";
	   	my $tempFile			= basename( $file );	
		write_complete_log("$depolyProgress .../$tempFile", $verboseMode);   
		
		my $fileSpaceReplacedPercentageTwenty   	= basename( $file );
		   $fileSpaceReplacedPercentageTwenty       =~ tr/%/ /;
		   $fileSpaceReplacedPercentageTwenty       =~ s#\s#%20#g;	
		my $folderSpaceReplacedPercentageTwenty		= $$inputFeedHref{'targetFolder'};
		   $folderSpaceReplacedPercentageTwenty     =~ tr/%/ /;
		   $folderSpaceReplacedPercentageTwenty	 	=~ s#\s#%20#g;
		   
	    # Search for file exist
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
	    $cmd .= "-X GET \"$server/api/storage/$$inputFeedHref{'repo'}/$folderSpaceReplacedPercentageTwenty/$fileSpaceReplacedPercentageTwenty\" ";
	    $cmd .= "--silent --output $devNul --write-out \"%{http_code}\"";
	    my $status1 = `$cmd`;

	    # HTML output Status code
		# 200="OK"
		# 201="Created"
		# 202="Accepted" 
		# 203="Non-Authoritative Information"
		# 204="No Content" 
		# 400="Bad Request"
		# 401="Unauthorized"
		# 403="Forbidden"
		# 404="Not Found"
		# 405="Method Not Allowed"
		# 406="Not Acceptable"
		# 500="Internal Server Error"
		# 501="Not Implemented"
		# 503="Service Unavailable"
		# 505="HTTP Version Not Supported" 

	    # Search for checksum
        $cmd = set_curl_command($no_proxy, $userId, $password, 0);
	    $cmd .= "-X PUT -H \"X-Checksum-Deploy:true\" -H \"X-Checksum-Sha1:$sha1Value\" -H \"X-Checksum-Md5:$md5Value\" --write-out \"%{http_code}\" --silent --output $devNul ";
	    $cmd .= "\"$server/$$inputFeedHref{'repo'}/$folderSpaceReplacedPercentageTwenty/$fileSpaceReplacedPercentageTwenty\"";
	    my $status2 = `$cmd`;
	    
	    if ($status2 eq "404") 
	    { # checksum not found -> deploy/upload file
	    	if ($status1 eq "404" || $force) 
	    	{
	      		# Upload
                $cmd = set_curl_command($no_proxy, $userId, $password, 0);
	       		$cmd .= "-H \"X-Checksum-Sha1:$sha1Value\" -H \"X-Checksum-Md5:$md5Value\" ";
	       		$cmd .= "--write-out \"%{http_code}\" --silent --output $devNul -T \"$file\" \"$server/$$inputFeedHref{'repo'}/$folderSpaceReplacedPercentageTwenty/$fileSpaceReplacedPercentageTwenty\"";
	       		my $statusUpload = `$cmd`; # upload if file not exist or force enabled

	       		if ($statusUpload =~ /^2/) 
	       		{ # upload ok , print status
	       			if ($status1 ne "404")
	    			{
						write_complete_log(" - Upload ok(File exist and overwritten): $statusUpload\n", $verboseMode);
						$overwrittenArtifact++;
					}
	    			else
	    			{
						write_complete_log(" - Upload ok: $statusUpload\n", $verboseMode);
					}
					$uploadedArtifact++; 
	        	}
	      		else
	      		{ # error from upload
					write_complete_log(" - \n ERROR during upload: $statusUpload\n", $verboseMode);
	        		$errorString .= "Error upload: $statusUpload - $file\n";
	      		}
	    	}
	    	elsif (($status1 =~ /^4/) || ($status1 =~ /^5/)) 
	    	{ # other error from file search, client error 4xx or server error 5xx
				write_complete_log(" - \n ERROR during search for file: $status1\n", $verboseMode);
	      		$errorString .= "Error file search: $status1 - $file\n";
	    	}
	    	else  
	    	{
				write_error_log(" - \n ERROR during upload: File exist with same name. If you want to overwrite file, select force option (-force) and user should have DELETE permission on $$inputFeedHref{'repo'}\n", $verboseMode);
	    		write_error_log("\n===========================================================================================================\n\n", $verboseMode);
	    		exit(1);
	    	}
	    }
	    elsif (($status2 =~ /^4/) || ($status2 =~ /^5/)) 
	    { # other error from checksum, client error 4xx or server error 5xx
			write_complete_log(" - \n ERROR during search for checksum: $status2\n", $verboseMode);
	    	$errorString .= "Error checksum: $status2 - $file\n";
	    }
	    else 
	    { # should be ok, print status for info
	    	if ($status1 eq "404")
	    	{
	    		write_complete_log(" - Upload ok : $status2\n", $verboseMode);
				#write_complete_log("Upload ok(Checksum exist but in different name or location): $status2\n");	# checksum matched but in different name or location, files will not be uploaded only mapped to new location or name             
				$uploadedArtifact++;                 																   			# only counted if file is not there in current version eventhough checksum is availabe somewhere else
	    	}
	    	else
	    	{
	    		write_complete_log(" - Checksum ok: $status2\n", $verboseMode);    							                   	# checksum matched under current folder, files will not be uploaded only mapped
	    	}  
	    }
        get_progress_percentage(int($def_percentage_counter * $fileUploadProgress), "Upload", $totalNoOfVersions, $versionCount) if (not $verboseMode);
	}
}

###################################################################################################################
# Search files for given patters : story-62230
#
sub searchFile
{
	my %inputFeed			= @_; 			 		
	my $fileBaseComponent 	=  basename($inputFeed{'fileArtifact'});
	my $fileRootComponent 	=  dirname($inputFeed{'fileArtifact'});
	   #$fileRootComponent   =~ s#^(\/|\.)$##;
       #$fileRootComponent 	=~ s#\*\*#.*?#g;

	my (@fileList, @filesToUpload)	= ();
	if ( $^O =~ /mswin/i )
	{
		my $temp	= $fileRootComponent;
		   $temp    =~ s#\/#\\#g;
		@fileList 	= `cmd /c dir /B /A-D "$temp"`;
	}
	else 
	{
		@fileList	= `find $fileRootComponent -maxdepth 1 -type f`;
	}
	#print Dumper \@fileList;
  	# check for no search result
	if ( scalar @fileList == 0 )
	{
		write_complete_log( "\nINFO: No 'result' found for given search: $inputFeed{'fileArtifact'} or $fileRootComponent is empty\n" );
		#return( 1 );
		return @filesToUpload;
	}
  	
    for my $fileName ( @fileList ) 
  	{
  		chomp $fileName;
  		$fileName = basename( $fileName );

  		#if ( $fileName =~ /^\./ || $fileName =~ /^_content.sha1/ )
  		#{
  		#	next ;
  		#}
  		#print $fileName;
  		my $regex = glob_to_regex( $fileBaseComponent );
  		if ( $fileName =~ $regex )
  		{
  			push( @filesToUpload, "$fileRootComponent/$fileName" );
  		}	
  	}
  
  	if ( scalar @filesToUpload == 0 )
  	{
  		write_complete_log( "\nINFO: No 'match' found for given search: $inputFeed{'fileArtifact'}\n" );
		#return( 1 );
  	}
  	#print Dumper \@files;
	#return(0);
	return @filesToUpload;
}

#################################################################################################################
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly : story-52826
#
sub scanArgs
{
	my ( $h, %inputFeed, $configFile, $verbose, $useproxy );

	GetOptions(
  				'h'		=> \$h,
  				'force' => \$force,
  				'r=s'	=> \$inputFeed{'repo'},
  				'i=s'	=> \$inputFeed{'fileArtifact'},
  				'c=s'	=> \$inputFeed{'targetFolder'},
  				'f=s'   => \$configFile,
  				'verbose'    => \$verbose,
  				's=s'	=> \$server,
  				'u=s'	=> \$userId,
  				'p=s'	=> \$password,
                'useproxy'    => \$useproxy,				
  			) or do {
  						write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  						write_console( $usage );
						write_error_log("\n===========================================================================================================\n\n");
						exit(1);
  					}; 

	$repository_name = $inputFeed{'repo'};
	if(scalar @ARGV)
	{
		write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
		write_console( $usage );
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}
  	if ($h) 
  	{
  		write_error_log("\nINFO: Help message requested!\n");
   		write_console( $usage );
   		write_error_log("\n===========================================================================================================\n\n");
    	exit(0);
  	}

    if (not $verbose){$verboseMode = 0} else {$verboseMode = 1};	

  	if ($configFile) 
  	{ # read infos from file
  	#######################check is need here#########################################
    	if ( ($inputFeed{'targetFolder'}) || ($inputFeed{'fileArtifact'}) || ($inputFeed{'repo'}) ) 
    	{
    		write_complete_log("\nWARNING: Other arguments will be ignored when using -f\n\n", $verboseMode);
    	}
    	# normalise path
  		$configFile = normalise_path($configFile);
  		
  		if ($configFile == 1)
  		{
  			write_error_log("\nERROR: Invalid config file: $configFile path!\n");
  			write_console( $usage );
  			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
  		}
    	if ((! -e $configFile) && (! -f $configFile))
    	{
    		write_error_log("\nERROR: config file: $configFile not exist!\n");
			write_console( $usage );
			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
    	}
    	open(CONFIG, "<$configFile") or die "\n$configFile cannot be opened!\n\n===========================================================================================================\n\n";
    	my @lines = <CONFIG>;
    	close(CONFIG);
    	
    	my $lineNumber = 0;
    	foreach my $line (@lines) 
    	{
    		$lineNumber++;
    		next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
    		chomp $line;
    		my ( %inputFeedCfg, $argumentCount );
    		$argumentCount = ( ( $inputFeedCfg{repo},$inputFeedCfg{targetFolder},$inputFeedCfg{fileArtifact} ) = split( /::/,$line ) ) ;
    		if ($argumentCount > $configFileArgumentsCount )
    		{
    			write_error_log("\nERROR: Extra arguments in config file at line $lineNumber !\n");
				write_console( $usage );
				write_error_log("\n===========================================================================================================\n\n");
  				exit(1);
      		}
      		#remove space before and after the input arguments
			normaliseArguments(\%inputFeedCfg);
			if (not defined $repository_name)
			{
				$repository_name = $inputFeedCfg{repo};
			}

    		# arguments check      
			argumentCheck(\%inputFeedCfg, $lineNumber);
			
  			$inputFeedCfg{fileArtifact}   = normalise_path($inputFeedCfg{fileArtifact});
  		  	if ( $inputFeedCfg{fileArtifact} == 1 )
	  		{
	  			write_error_log("\nERROR: Invalid source file: $inputFeedCfg{fileArtifact} path at line $lineNumber !\n");
	  			write_console( $usage );
	  			write_error_log("\n===========================================================================================================\n\n");
	  			exit(1);
	  		}
			
  			push( @argumentList,\%inputFeedCfg );
    	}
  	}
  	else 
  	{ 
  		#remove space before and after the input arguments
		normaliseArguments(\%inputFeed);
  		# arguments check      
		argumentCheck(\%inputFeed);
    	$inputFeed{'fileArtifact'}   = normalise_path($inputFeed{'fileArtifact'});
    	if ( $inputFeed{'fileArtifact'} == 1 )
	  	{
	  		write_error_log("\nERROR: Invalid source file: $inputFeed{'fileArtifact'} path!\n");
	  		write_console( $usage );
	  		write_error_log("\n===========================================================================================================\n\n");
	  		exit(1);
	  	}
		
		push( @argumentList,\%inputFeed );
  	}

  	normaliseArguments(\%inputFeed);
	
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
        if ( (not $userId) && ($password) ) 
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
# Remove space before and after the arguments and normalise slashes : story-52826
#
sub normaliseArguments
{
	my $arguments = shift;
	
	foreach my $keyArgument (keys %{$arguments})
	{
		$$arguments{$keyArgument} 		=~ s#^\s*##;
		$$arguments{$keyArgument} 		=~ s#\s*$##;
	}
	#$$arguments{fileArtifact} 			=~ s#\s#%20#g;
			$$arguments{targetFolder} 	=~ s#\\#\/#g;
	1 while $$arguments{targetFolder} 	=~ s#^(\\|\/)##g;
  	1 while $$arguments{targetFolder} 	=~ s#(\\|\/)$##g;
  	1 while $$arguments{targetFolder} 	=~ s#\\\\|\/\/#\/#g;
	return($arguments);
}

#################################################################################################################
# check arguments are passed correctly : story-52826
#
sub argumentCheck
{
	my $inputFeed 	= shift;
	my $lineNumber 	= shift;
	
  	if ((!$$inputFeed{'repo'}) || (!$$inputFeed{'fileArtifact'}) || (!$$inputFeed{'targetFolder'})) 
  	{
    	my $errorString  = "\nERROR: Arguments ";
    	   $errorString .= '-r <repo>, ' if (!$$inputFeed{'repo'});
    	   $errorString .= '-f <fileArtifact>, ' if (!$$inputFeed{'fileArtifact'});
    	   $errorString .= '-c <targetFolder>' if (!$$inputFeed{'targetFolder'});
    	   $errorString  =~ s#, $##;
    	   
  		($lineNumber) ? ($errorString .= " missing at line $lineNumber !\n") : ($errorString .= " missing!\n");
  		write_error_log("$errorString");
    	write_console( $usage );
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# check for spaces in artifact target folder names
  	if ( $$inputFeed{'targetFolder'} =~ /\s/ ) 
  	{
    	write_error_log("\nERROR: Artifactory target folder shall not contain spaces, please check argument (-c <targetFolder>)\n");
    	write_console( $usage );
		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# check if source file exists
  	if ( basename( $$inputFeed{'fileArtifact'} ) !~ /[*?{[]/ )
  	{
		if (! -f $$inputFeed{'fileArtifact'} ) 
		{
    		write_error_log("\nERROR: Source file: $$inputFeed{'fileArtifact'} does not exist.\n");
    		write_console( $usage );
		 	write_error_log("\n===========================================================================================================\n\n");
    		exit(1);
		}
  	}
}

###################################################################################################################
# File validation check : story-63369
#
sub folderValidationCheck
{
	my %inputFeed 			= @_;

	my $folderWithoutSpace  = $inputFeed{'targetFolder'};
    $folderWithoutSpace  =~ s#\s#%20#g;

    my $cmdToFolderValidate	= set_curl_command($no_proxy, $userId, $password, 0);
	$cmdToFolderValidate .= "-sS -X GET \"$server/api/storage/$inputFeed{'repo'}/$folderWithoutSpace\"";
	my $resultJson = `$cmdToFolderValidate`;
	my $decodeResult = decode_json( $resultJson );

	if ( ref $$decodeResult{'errors'} ne 'ARRAY' )
	{
		if ( ref $$decodeResult{'children'} ne 'ARRAY')
		{
			write_error_log("ERROR: Given targer component '$inputFeed{'targetFolder'}' is not a valid folder.\n");
			$errorString .= "ERROR: Given targer component '$inputFeed{'targetFolder'}' is not a valid folder.\n";
			return(1);
		}
	}
	else
	{
		write_error_log("WARNING: Given target component '$inputFeed{'targetFolder'}' is not available in given repository '$inputFeed{'repo'}', Target component will be created\n\n", $verboseMode);
	}
	return(0) ;
}