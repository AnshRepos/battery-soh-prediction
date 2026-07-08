#############################################################################################################################################################
#																																							#
# FILE			:   download_single_artifact.pl																												#
#																																							#
# DESCRIPTION	:   Download a single file from artifactory repository																						#
#																																							#
# USAGE			:   download_single_artifact.pl [-h] ( ( -r <repo> -c <fileArtifact> -o <outputFolder> ) | -f <configFile> ) [ -mode <fast|update>] 		#
#												[ -verbose ] [ -s <server> -u <userId> -p <password> -useproxy ]											#
#																																							#
# ARGUMENTS		:   See usage																																#
#																																							#
# COPYRIGHT		:   (c) 2014 Robert Bosch GmbH																												#
# HISTORY		:																																			#
#																																							#
# Date         	| Author                 		| 	Modification																							#
# 23.10.2014   	| M.Schoenfelder (ext)   		| 	Initial version																							#
# 07.11.2014   	| M.Schoenfelder (ext)   		| 	Option S for curl to ommit error messages other than http_code											#
# 22.06.2015   	| M.Schoenfelder (ext)   		| 	no virtual repo in new setup of artifactory server, user and pwd required								#
#                                         			read server, user and pwd from artifactory config file													#
# 01.03.2016	| Saddam hussain A 	(RBEI/ECA2)	| 	Adapt to new config file ( check settings, normalise path function), multi file download implemented:	#
#													story-52827																								#
# 15.06.2016 	| Saddam hussain A  (RBEI/ECA2)	| 	Added functionality to process Ant wild cards : story-62230												#
#													checkusm based download as download_artifact.pl added : story-62233										#
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled windows based execution : feature-76330                                                         #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled verbose mode and progress bar: feature-76327                                                    #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled mac based execution : feature-76330                                                             #
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		| 	Modified code to handle empty line with spaces in config file					 						#
# 04.03.2017	| Sounak Patra (RBEI/ECA2)		| 	Modified code to download artifacts from remote repository					 							#
# 07.04.2017	| Sounak Patra (RBEI/ECA2)      | 	Modified code to handle connection timeout																#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | 	Made modifications to check latest script version: story-165111											#
# 05.09.2017	| Sounak Patra (RBEI/ECA2)		| 	Added option to generate file to store md5 values: story-178336								 			#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		| 	Added feature to stop execution of older scripts: story-185699											#
# 20.12.2017	| Sounak Patra (RBEI/ECA2)		| 	Improved error handling, logging for caching files in remote repository and								#
#													md5 checksum validation: story-222017																	#
# 18.03.2019	| Sounak Patra (RBEI/ECQ2)		|   Added noproxy option in curl                                                                            #
# 18.10.2019	| Sounak Patra (RBEI/ECQ2)		|   Added missing argument in method get_server_generated_md5_checksum_value                                #
#
# 14.04.2021	| Gerhard Kiegeland (XC-CI1/ESY)|   Improved caching mechanism, cache only if file not cached. Speedup if config file is used               #
# 22.04.2021	| Gerhard Kiegeland (XC-CI1/ESY)|   Implemement a retry function if caching or download fails                                               #
# 09.07.2021	| Gerhard Kiegeland (XC-CI1/ESY)|   RTC1-1169903 search and cache files allway even realname is given (no wild cards)                       #
#                                                                                                                                                           #
#############################################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use Getopt::Long;
use File::Basename;
use Text::Glob qw( glob_to_regex );

# Usage
my $usage = "
Usage:
  perl $0 [-h] ( ( -r <repo> -c <fileArtifact> -o <outputFolder> ) | -f <configFile> ) [ -verbose ] [-generatemd5] [ -mode <fast|update>] [ -s <server> -u <userId> -p <password> -useproxy ]

  Download a single file from artifactory.

       -h                      : Print helper message
       -f    <configFile>      : Configuration file with all argument information
       -c    <fileArtifact>    : File to be downloaded, cannot be used with -f
       -o    <outputFolder>    : Output folder, cannot be used with -f
       -r    <repo>            : Artifactory repository, cannot be used with -f
       -verbose                : Verbose mode
       -generatemd5            : Generates _content.md5 file,
       -mode <fast|update>     : Mode to check existing files before downloading:
				    fast   - default: download the missing/deleted files in the output folder. 
				             Script does not check for file content change in the output folder.
				             The existent files in output folder will not be deleted if those files are not available in repository. 
				    update - update the output folder with changed/deleted files. 
				             The existent files in output folder will not be deleted if those files are not available in repository.
       -s    <server>          : Artifactory Server (optional, will override config file)
       -u    <userId>          : Artifactory User ID (optional, will override config file)
       -p    <password>        : Artifactory Password (optional, will override config file)
       -useproxy               : Uses current proxy settings (optional, will override config file)'
       
  Format of <configFile>:
	# used with comments
	# one line per download; items seperated by two colon; all arguments are mandatory
	Repository::outputFolder::fileArtifact
       	
  When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!
  
  Wildcards:
    Supports Ant wild cards '?' matches single and '*' matches zero or more characters, using other wild card characters will give unreliable results.
    Supports Alternation( example.{foo,bar,baz} matches example.foo, example.bar, and example.baz )
    Supports Character sets/ranges( example.[ch] matches example.c and example.h, demo.[a-c][c-e] matches demo.ac, demo.bd, and demo.ce )
  \n";

# arguments
my ($server, $userId, $password, $verboseMode, $generatemd5, $repository_name, $no_proxy);
my $mode						= 'fast';
my $configFileArgumentsCount 	= 3;  		# Repository::outputFolder::fileArtifact
my @argumentList				= ();
my ( $artifactToDownload, $downloadedArtifact, $failedArtifact, $failedValidationFileCount) = ( 0, 0, 0, 0 );
my $debug						= 0;

# other vars
my %filesToDownload       		= ();   # list of files with checksum info (art, local, from existing _content file)
my @finalChecksumFileList		= ();
my $autoAnswer   				= $ENV{_SET_ENV_AUTO_ANSWER};
my $errorString 				= "";
my $downloadLogFile       		= 'download.log';
my $errorLogFile		   		= 'download_error.log';
my $startTime					= time();
my $endTime						= 0;
#my $configLinesCount			= 0;
#my $configLinesDownloadProgress	= 0;
#my $configLinesFixedLength		= 0;
my %allreadyLoadedJsonList      = ();
my @file_to_cache               = ();

# Create log file
my $artifactoryLogDir = create_log_file( $downloadLogFile, $errorLogFile );
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

if ($mode =~ /fast/i){
	write_error_log("On Server\t\t: $server\nOperation( mode )\t: Download single file( fast )\n", $verboseMode)
}
elsif ($mode =~ /update/i){
	write_error_log("On Server\t\t: $server\nOperation( mode )\t: Download single file( update )\n", $verboseMode)
}
print "On Server\t: $server\n" if (not $verboseMode);

CONFIG:	
	my $versionCount = 0;
	print "\n";
	foreach my $inputFeedHref (@argumentList) 
	{
		$versionCount ++;
		@file_to_cache = ();
		# Exit if server is not pingable
		if( check_settings( $server, $userId, $password, $$inputFeedHref{'repo'}, $no_proxy) ) 					# source repository existence check
		{
			my 	$writeString			= "\nERROR: Source repository not found or user not having read permission to ";
			$writeString 	       .= "repository: $$inputFeedHref{'repo'} in artifactory server: $server\n\n";
		   	write_error_log($writeString);
		   	$errorString               .= $writeString;
		   	next CONFIG;
		}
  		
  		# create outputFolder if not existent, check for user permissions
  		write_complete_log("\n--------- Processing $$inputFeedHref{'outputFolder'}... ---------\n", $verboseMode);
  		if (! -d $$inputFeedHref{'outputFolder'}) 
  		{
			my $parentPath = dirname( $$inputFeedHref{'outputFolder'} );
    		while ( ! -d $parentPath ) 
    		{
      			$parentPath = dirname($parentPath);
   			}
    		# check if folder is writeable by user
    		if( -w $parentPath )
  			{
  				eval { mkpath( $$inputFeedHref{'outputFolder'} ) };
				if ($@)
				{
					write_error_log("\nERROR: Not able to create path $$inputFeedHref{'outputFolder'}, Message: $!\n\n", $verboseMode);
					write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  					exit(1);
				}
				else
				{
					write_complete_log("INFO: Output folder not exist, Created\n", $verboseMode);
				}
  			}
  			else
  			{
  				write_error_log("\nERROR: Output folder not exist, User not having permission to create it.\n", $verboseMode);
  				write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  				exit(1);
  			}
  		}
  		else
  		{
  			#use File::stat ;
			#printf "%o\n", stat($$inputFeedHref{'outputFolder'}) -> mode & 07777;
  			if ( ! -w $$inputFeedHref{'outputFolder'} )
  			{
  				write_error_log("\nERROR: Output folder: $$inputFeedHref{'outputFolder'} exist, User not having write permission to perform download.\n", $verboseMode);
  				write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  				exit(1);
  			}
  			else
  			{
  				write_complete_log("INFO: Output folder exist, Proceeding\n", $verboseMode);
  			}
  		}
  		
  		%filesToDownload        = ();                            # reset files and finalChecksumFileList for each new download using config file
  		@finalChecksumFileList	= ();
  		my $fileWithSpace  		= $$inputFeedHref{'fileArtifact'};
  		   $fileWithSpace  		=~ s#%20# #g;
  		   
  	   	my $writeString    		= "\nProcessing download from $$inputFeedHref{'repo'}/$fileWithSpace to $$inputFeedHref{'outputFolder'}\n\n";
		write_complete_log($writeString, $verboseMode); 
		my $response = searchFile( %{$inputFeedHref} );
		next CONFIG if ($response);

  		if ( $$inputFeedHref{'fileArtifact'} !~ /[*?{[]/ )        # call for search all file function only if the given file has wildcard characters.
  		{
  			# file validation 
  			next CONFIG if ( fileValidationCheck( $inputFeedHref ) );
  			my $response = getFileChecksum( %{$inputFeedHref} );
  			next CONFIG if ($response);
  		}
  		
  		# not first download, evaluate checksums and change files list for download accordingly
  		if (-f $$inputFeedHref{'outputFolder'}."/_content.sha1") 
  		{
    		# create local checksum file if requested
    		if ($mode =~ /update/i) 
    		{
#    		  	createLocalChecksumFileLinux( %{$inputFeedHref} ) if ($^O =~ /linux/i || $^O =~ /cygwin/i);
#      			createLocalChecksumFileMswin( %{$inputFeedHref} ) if ($^O =~ /mswin/i);
      			if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i){
      				createLocalChecksumFileLinux( %{$inputFeedHref} )
      			}
      			elsif ($^O =~ /mswin/i){
      				createLocalChecksumFileMswin( %{$inputFeedHref} )
      			}
      			fillContentSha( %{$inputFeedHref} );
    		}
    		else
    		{
    			fillContentSha( %{$inputFeedHref} );
    		}
    		if ( $debug )
  			{
  				print "\n";
  				print Dumper \%filesToDownload if $debug ;
  			}
    		diffChecksums( $$inputFeedHref{'outputFolder'} );
    
    		# remove old file before renaming new created artifactory checksum file
    		rename($$inputFeedHref{'outputFolder'}."/_content.sha1",$$inputFeedHref{'outputFolder'}."/_content.sha1.keep");
  		}
  		else
  		{
  			# create local checksum file if requested
    		if ($mode =~ /update/i) 
    		{
#    		  	createLocalChecksumFileLinux( %{$inputFeedHref} ) if ($^O =~ /linux/i || $^O =~ /cygwin/i);
#      			createLocalChecksumFileMswin( %{$inputFeedHref} ) if ($^O =~ /mswin/i);
      			if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i){
      				createLocalChecksumFileLinux( %{$inputFeedHref} )
      			}
      			elsif ($^O =~ /mswin/i){
      				createLocalChecksumFileMswin( %{$inputFeedHref} )
      			}
      			#fillContentSha( %{$inputFeedHref} );
    		}

    		if ( $debug )
  			{
  				print "\n";
  				print Dumper \%filesToDownload if $debug ;
  			}
    		diffChecksums( $$inputFeedHref{'outputFolder'} );	
  		} 
  		  		
  		# download files according to %filesToDownload
  		download($inputFeedHref, $versionCount, scalar @argumentList);
	}
	print "\n";

# Calculate time to complete download
$endTime 		= time();
my $duration 	= $endTime - $startTime;
my $minutes 	= ( int($duration / 60) ) % 60;
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
  	write_error_log("\nTotal no. of files: $artifactToDownload, downloaded: $downloadedArtifact, failed: $failedArtifact\n");
  	if ($generatemd5 && $failedValidationFileCount != 0)
  	{
  		write_error_log("\nMd5 checksum validation failed for $failedValidationFileCount file/files\n");
  	}
  	#printf("Time taken HH:MM:SS %02d:%02d:%02d\n\n",$hours,$minutes,$seconds);
  	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nDownload log       : $artifactoryLogDir$downloadLogFile\n"; 
	print "Error log          : $artifactoryLogDir$errorLogFile\n";
  	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(1);
}
else 
{
	write_error_log("\nTotal no. of files: $artifactToDownload, downloaded: $downloadedArtifact, failed: $failedArtifact\n");
  	if ($generatemd5 && $failedValidationFileCount != 0)
  	{
  		write_error_log("\nMd5 checksum validation failed for $failedValidationFileCount file/files\n");
  	}
	#printf("Time taken HH:MM:SS %02d:%02d:%02d\n\n",$hours,$minutes,$seconds);
	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nDownload log       : $artifactoryLogDir$downloadLogFile\n"; 
	print "Error log          : $artifactoryLogDir$errorLogFile\n";
	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(0);
}

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# download files
#
sub download
{
	my $inputFeed 				= shift;
  	my $versionCount			= shift;
  	my $totalNoOfVersions 		= shift;
	my $rootComponent			= dirname( $$inputFeed{'fileArtifact'} );
	   $artifactToDownload 	   += scalar keys(%filesToDownload);
	my $fileCount				= scalar keys(%filesToDownload);
	my $fileDownloadProgress	= 0;
	my @md5_file_list;
	my @md5_error_list;
	
  	my $def_percentage_counter = 0;
  	   $def_percentage_counter = (100 / scalar(keys(%filesToDownload))) if (scalar(keys(%filesToDownload)));	

	#print Dumper \%filesToDownload;
	write_complete_log("Downloading $fileCount files...\n", $verboseMode) if scalar keys %filesToDownload;
	
	foreach my $file ( keys %filesToDownload )
	{
		$fileDownloadProgress++;
		my $fileWithoutSpace 	= $file;
		   $fileWithoutSpace 	=~ s#\s#%20#g;
		
		my $fileWithSpace 	 	= $file;
	   	   #$fileWithSpace	 	=~ s#(.*/)(.*)$#$2#;	
	   	   #$fileWithSpace	 	=~ s#%20# #g;
	   	my $downloadProgress	= "($fileDownloadProgress\/$fileCount)";

	   	write_complete_log("$downloadProgress ...$$inputFeed{'repo'}/$rootComponent/$fileWithSpace", $verboseMode);
    
        my $cmd = set_curl_command($no_proxy, $userId, $password, 1);
		# [Incident: 2132936]
        #$cmd .= "-sS -f -L --write-out \"%{http_code}\" \"$server/$$inputFeed{'repo'}/$rootComponent/$fileWithoutSpace\" -o \"$$inputFeed{'outputFolder'}/$fileWithSpace\"";
		$cmd .= "-f -L \"$server/$$inputFeed{'repo'}/$rootComponent/$fileWithoutSpace\" -o \"$$inputFeed{'outputFolder'}/$fileWithSpace\"";
		my $result = `$cmd`;

		if ($? eq "0") 
		{	
			my $digit = (split //, $result)[0];
			if ($digit == 4)
			{
				write_complete_log(" - $result - ERROR\n", $verboseMode);
				$errorString .= "ERROR download: $fileWithSpace\n";
				$failedArtifact++;
			}
			else
			{
				write_complete_log(" - $result - ok\n", $verboseMode);
				my $checksumFile = "$filesToDownload{$file}{sha1_art} \*\./$fileWithSpace\n";
				push (@finalChecksumFileList,$checksumFile);
				$downloadedArtifact++;
	
	    		if (($generatemd5) && (-e "$$inputFeed{outputFolder}/$fileWithSpace"))
	    		{
		    		my $md5_value_local = get_hash_value('MD5', "$$inputFeed{outputFolder}/$fileWithSpace");
		    		my $md5_value_server = get_server_generated_md5_checksum_value($server, $userId, $password, $no_proxy, $$inputFeed{'repo'}, "$rootComponent/$fileWithoutSpace");
					if ($md5_value_local ne $md5_value_server)
					{
						push(@md5_error_list, $md5_value_local . " " . $md5_value_server . " *./" . $fileWithSpace . "\n");
					}
		    		my $md5_content = $md5_value_local . " *./" . $fileWithSpace . "\n";
		    		push (@md5_file_list, $md5_content);
	    		}					
			}
		}
		else
		{
			write_complete_log(" - $result - ERROR\n", $verboseMode);
			$errorString .= "ERROR download: $fileWithSpace\n";
			$failedArtifact++;
		}
	   	get_progress_percentage(int($def_percentage_counter * $fileDownloadProgress), "Download", $totalNoOfVersions, $versionCount) if (not $verboseMode); 
	}
	# Write successfully downloaded files and checksums to the content.sha1 file
  	my $contentSha1File = "$$inputFeed{'outputFolder'}/_content.sha1";
  	write_to_file($contentSha1File, @finalChecksumFileList);

  	# Writes MD5 value to _content_md5_file
  	if ($generatemd5)
  	{
  		my $content_md5_file = "$$inputFeed{outputFolder}/_content.md5";
  		my $content_md5_error_file = "$$inputFeed{outputFolder}/_content_error.md5";
	  	my @file_names = keys %filesToDownload;
	  	generate_md5_file(\@md5_file_list, \@file_names, $content_md5_file);
	  	generate_md5_error_file(\@md5_error_list, $content_md5_error_file);
	  	$failedValidationFileCount += scalar @md5_error_list;
  	}
}

#################################################################################################################
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly : story-52827
#
sub scanArgs
{
  	my (%inputFeed, $configFile, $verbose, $generatemd5file, $useproxy, $h);
  	GetOptions(
  				'h'		=> \$h,
  				'r=s'	=> \$inputFeed{'repo'},
  				'c=s'	=> \$inputFeed{'fileArtifact'},
  				'o=s'	=> \$inputFeed{'outputFolder'},
  				'f=s'   => \$configFile,
  				'verbose'    => \$verbose,
  				'generatemd5'    => \$generatemd5file,
  				'mode=s'=> \$mode,
  				's=s'	=> \$server,
  				'u=s'	=> \$userId,
  				'p=s'	=> \$password,
                'useproxy'    => \$useproxy,
  				'x'		=> \$debug	
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
  	if (not $generatemd5file){$generatemd5 = 0} else {$generatemd5 = 1};
  	
  	if ( !(($mode =~ /^fast$/i) || ($mode =~ /^update$/i)) ) 
  	{
  		write_error_log("\nERROR: Selected mode is not supported, select fast or update\n");
    	write_console( $usage );
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}

	if ($configFile) 
  	{ # read infos from file
  	#######################check is need here#########################################
    	if ( ($inputFeed{'outputFolder'}) || ($inputFeed{'fileArtifact'}) || ($inputFeed{'repo'}) ) 
    	{
    		write_complete_log("\nWARNING: Other arguments will be ignored when using -f\n\n");
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
    	open(CONFIG, "<$configFile") or die "$configFile cannot be opened!\n\n===========================================================================================================\n\n";
    	my @lines = <CONFIG>;
    	close(CONFIG);
    
    	my $lineNumber = 0;
    	foreach my $line (@lines) 
    	{
    		$lineNumber++;
    		next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
    		chomp $line;
    		my ( %inputFeedCfg, $argumentCount );
    		$argumentCount = (($inputFeedCfg{repo},$inputFeedCfg{outputFolder},$inputFeedCfg{fileArtifact}) = split(/::/,$line)) ;
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

      		# generic arguments check 
    		argumentCheck(\%inputFeedCfg, $lineNumber);
    		
  			$inputFeedCfg{outputFolder}   = normalise_path($inputFeedCfg{outputFolder});
  		  	if ( $inputFeedCfg{outputFolder} == 1 )
	  		{
	  			write_error_log("\nERROR: Invalid Output file: $inputFeedCfg{outputFolder} path at line $lineNumber !\n");
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
  		
    	$inputFeed{'outputFolder'}   = normalise_path($inputFeed{'outputFolder'});
    	if ( $inputFeed{'outputFolder'} == 1 )
	  	{
	  		write_error_log("\nERROR: Invalid Output file: $inputFeed{'outputFolder'} path!\n");
	  		write_console( $usage );
	  		write_error_log("\n===========================================================================================================\n\n");
	  		exit(1);
	  	}
    	#print Dumper \%inputFeed;
		push( @argumentList,\%inputFeed );
  	}
	
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
            write_console( $usage );
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
# check arguments are passed correctly : story-52827
#
sub argumentCheck
{
	my $inputFeed 	= shift;
	my $lineNumber 	= shift;
	
  	if ((!$$inputFeed{'repo'}) || (!$$inputFeed{'fileArtifact'}) || (!$$inputFeed{'outputFolder'})) 
  	{
    	my $errorString  = "\nERROR: Arguments ";
    	   $errorString .= '-r <repo>, ' if (!$$inputFeed{'repo'});
    	   $errorString .= '-c <fileArtifact>, ' if (!$$inputFeed{'fileArtifact'});
    	   $errorString .= '-o <outputFolder>' if (!$$inputFeed{'outputFolder'});
    	   $errorString  =~ s#, $##;
    	   
  		($lineNumber) ? ($errorString .= " missing at line $lineNumber !\n") : ($errorString .= " missing!\n");
  		write_error_log("$errorString");
    	write_console( $usage );
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
}

#################################################################################################################
# Remove space before and after the arguments and normalise slashes : story-52827
#
sub normaliseArguments
{
	my $arguments = shift;
	
	foreach my $keyArgument (keys %{$arguments})
	{
		$$arguments{$keyArgument} 		=~ s#^\s*##;
		$$arguments{$keyArgument} 		=~ s#\s*$##;
	}
			$$arguments{'fileArtifact'} =~ s#\s#%20#g;
			$$arguments{'fileArtifact'} =~ s#\\#\/#g;
	1 while $$arguments{'fileArtifact'} =~ s#^(\\|\/)##g;
  	1 while $$arguments{'fileArtifact'} =~ s#(\\|\/)$##g;
  	1 while $$arguments{'fileArtifact'} =~ s#\\\\|\/\/#\/#g;
	return($arguments);
}

###################################################################################################################
# File validation check : story-52827
#
sub fileValidationCheck
{
	my $inputFeed = shift;	
    my $cmdToFileValidate = set_curl_command($no_proxy, $userId, $password, 1);
    $cmdToFileValidate .= "-sS -X GET \"$server/api/storage/$$inputFeed{'repo'}/$$inputFeed{'fileArtifact'}\"";
	my $resultJson = `$cmdToFileValidate`;
	my $decodeResult = decode_json( $resultJson );

	if ( ref $$decodeResult{errors} ne 'ARRAY' )
	{
		if ( ref $$decodeResult{children} eq 'ARRAY')
		{
			my 	$fileWithSpace  = $$inputFeed{'fileArtifact'};
  		   		$fileWithSpace  =~ s#%20# #g;
			write_error_log("\nERROR: Given file artifact: $fileWithSpace to download is not a valid file or not available in given repository: $$inputFeed{'repo'}\n");
			$errorString .= "\nERROR: Given file artifact: $fileWithSpace to download is not a valid file or not available in given repository: $$inputFeed{'repo'}\n";
			return(1);
		}
	}
	else
	{
		my $fileWithSpace  = $$inputFeed{'fileArtifact'};
  		   $fileWithSpace  =~ s#%20# #g;
		write_error_log("\nERROR: Failed to validate file artifact: $fileWithSpace, Message: $$decodeResult{errors}[0]{message}\n");
		$errorString .= "\nERROR: Failed to validate file artifact: $fileWithSpace, Message: $$decodeResult{errors}[0]{message}\n";
		return(1);
	}
	#print Dumper $decodeResult;
	return(0) ;
}

###################################################################################################################
# Search files for given patters : story-62230
#
sub searchFile
{
	my %inputFeed			= @_; 			 		
	my $fileBaseComponent 	=  basename($inputFeed{'fileArtifact'});
	my $fileRootComponent 	=  dirname($inputFeed{'fileArtifact'});
	   $fileRootComponent   =~ s#^(\/|\.)$##;
	#$fileRootComponent 	=~ s#\*\*#.*?#g;
	my $fileListJson        = "";
	my $decodedFileList     = "";
	my $retry               = 0; # retries if caching take longer 
	my $MAX_RETRIES         = 10;

	my $cmd = set_curl_command($no_proxy, $userId, $password, 1);
	$cmd .= "--silent -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.FileList+json\" ";
	$cmd .= "\"$server/api/storage/$inputFeed{'repo'}/$fileRootComponent?list\"";

	while ($retry < $MAX_RETRIES) 
	{
		if (!defined($allreadyLoadedJsonList{$fileRootComponent})){
			cacheRemoteArtifacts(\%inputFeed);  
			$fileListJson = `$cmd`;
			$decodedFileList = decode_json($fileListJson);
		} else {
			$decodedFileList = $allreadyLoadedJsonList{$fileRootComponent};
		}
		$allreadyLoadedJsonList{$fileRootComponent} = $decodedFileList;
		
		if (defined $decodedFileList->{'errors'} ) 
		{
			$errorString .= "No download of $inputFeed{'fileArtifact'} possible:\n";
			write_console("\nError message : $decodedFileList->{'errors'}[0]{'message'}\n");
			return(1);
		}
		
		my @fileList = @{$decodedFileList->{'files'}};
		
		# check for no search result
		if ( scalar @fileList == 0 )
		{
			write_complete_log( "\nINFO: No 'result' found for given search: $inputFeed{'fileArtifact'}\n" );
			return( 1 );
		}
		
		for (my $i=0;$i<=$#fileList;$i++) 
		{
			#check for files
			if ($fileList[$i]{'folder'} == 0 )
			{  			
				my 	$filename = $fileList[$i]{'uri'};
					$filename =~ s#^\/##;
				my $regex = glob_to_regex( $fileBaseComponent );
				if ( $filename =~ $regex )
				{
					$filesToDownload{$filename}{'sha1_art'} = $fileList[$i]{'sha1'};
				}	
			}
			else
			{
				$errorString .= "Could not evaluate type (dir/file) of $fileList[$i]{'uri'}\n";
			}
		}
		if ( scalar keys %filesToDownload == 0 )
		{		
			$allreadyLoadedJsonList{$fileRootComponent} = undef;
			$retry++;
			if ($retry > $MAX_RETRIES -1) {
				write_complete_log( "\nINFO: No 'match' found after $MAX_RETRIES retries for given search: $inputFeed{'fileArtifact'}\n" );
				return( 1 );
			}
			write_complete_log( "INFO: Retry $retry to find 'match' for search: $inputFeed{'fileArtifact'}\n" );
		} else {
		$retry = $MAX_RETRIES;
		}
	} # end while retry
	#print Dumper \%filesToDownload;
	return(0);
}

#################################################################################################################
# get file list for version from artifactory : story-62233
# store dir names in array to 
# example of part of output for one file:
#   {
#     "uri" : "/S_STA8088.bin",
#     "size" : 606632,
#     "lastModified" : "2015-07-14T16:27:34.531+02:00",
#     "folder" : false,
#     "sha1" : "6dc16c83f12facd34c31cc5de85b222304e59ac3"
#   },
#
sub getFileChecksum
{
	my %inputFeed = @_;
	my $file	= basename( $inputFeed{'fileArtifact'} );

    my $cmd = set_curl_command($no_proxy, $userId, $password, 1);
    $cmd .= "--silent -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.FileList+json\" ";
    $cmd .= "\"$server/api/storage/$inputFeed{'repo'}/$inputFeed{'fileArtifact'}\"";
    my $fileDetailsJson = `$cmd`;
    my $decodedFileDetails = decode_json($fileDetailsJson);
	
  	if ( defined $decodedFileDetails->{'errors'} ) 
  	{
    	$errorString .= "No download of $inputFeed{'fileArtifact'} possible:\n";
    	write_console("\nError message : $decodedFileDetails->{'errors'}[0]{'message'}\n");
    	return(1);
  	}
  	$filesToDownload{$file}{'sha1_art'} 	= $$decodedFileDetails{'checksums'}{'sha1'};
  	#print Dumper \%filesToDownload;
  	return(0);
}

#################################################################################################################
# fill array content_sha will info from sha_file (without line feed) : story-62233
#
sub fillContentSha
{
  	my %inputFeed  		= @_;
  	my $shaFile 		= $inputFeed{'outputFolder'}."/_content.sha1";
  	my $sourceFolder 	= $inputFeed{'outputFolder'};

  	open(SHA, "<$shaFile") or die "Could not open $shaFile for reading\n\n===========================================================================================================\n\n";
  	
  	while(my $line=<SHA>)
  	{
  	  	$line 							=~ s#[\r\n]##g;
    	my ($sha1,$file)  				=  split(/\s*\*\.\//,$line);
		$filesToDownload{$file}{'sha1_content'} 	= $sha1;
  	}
  	close(SHA);
  	#print Dumper \%filesToDownload;
}

#################################################################################################################
# create checksum file read from local files and fill values of sha_local : story-62233
#
sub createLocalChecksumFileLinux
{
  	my %inputFeed = @_;
  	
  	my $shaFile 			=  $inputFeed{'outputFolder'}."/_content.sha1.local";
  	open(SHASUM, ">$shaFile") or die "Could not open $shaFile\n\n===========================================================================================================\n\n";
  	foreach my $fileWithSpace ( keys %filesToDownload )
  	{
  		if ( $filesToDownload{$fileWithSpace}{'sha1_art'} ne '' )       # to check local checksum only for files which are to be downloaded rather checking for all files in output folder.
  		{  				
  			$fileWithSpace		=  $inputFeed{'outputFolder'}.'/'.$fileWithSpace;
	
  			if ( -f $fileWithSpace )
  			{
		 		my $cmd = "";
		  		if ($^O =~ /darwin/i){
		  			$cmd = "shasum \"$fileWithSpace\""
		  		}
		  		else{
		  			$cmd = "sha1sum \"$fileWithSpace\""
		  		}
				my $localFileChecksum = `$cmd`;
	   			$localFileChecksum =~ s#\Q$inputFeed{'outputFolder'}\E#\*\.#;
	   			print SHASUM $localFileChecksum;
	   			$localFileChecksum =~ s#[\r\n]##g;
	   			my ($sha1,$file) = split(/\s*\*\.\//,$localFileChecksum);
	  			#$file =~ s#\s#%20#g;
	  			$filesToDownload{$file}{sha1_local} = $sha1;
  			}
  		}
  	}
  	close(SHASUM);
}

#################################################################################################################
# create checksum file read from local files and fill values of sha_local : story-62233
#
sub createLocalChecksumFileMswin
{
	my %inputFeed = @_;
  	
  	my $dirWin 				= $inputFeed{'outputFolder'};
       $dirWin 				=~ s#\/#\\#g;
  	my $shaFile   		    = $dirWin."\\_content.sha1.local";
  	open(SHASUM, ">$shaFile") or die "Could not open $shaFile\n\n===========================================================================================================\n\n";
  	foreach my $fileWithSpace ( keys %filesToDownload )
  	{
  		if ( $filesToDownload{$fileWithSpace}{'sha1_art'} ne '' )       # to check local checksum only for files which are to be downloaded rather checking for all files in output folder.
  		{	
  		    $fileWithSpace		= $dirWin.'\\'.$fileWithSpace;
  			if ( -f $fileWithSpace )
  			{
	  			my $sha1 = get_hash_value('SHA1', $fileWithSpace);
				my $file = basename($fileWithSpace);
				print SHASUM "$sha1". " *./"."$file\n";			
    	  		$filesToDownload{$file}{sha1_local} = $sha1;
  			}
  		}
  	}
  	close(SHASUM);
}

#################################################################################################################
# compare difference in checksum for files : story-62233
#
sub diffChecksums
{
  	my $dir = shift;
  
  	foreach my $file (keys(%filesToDownload)) 
  	{	
  		next if ($file =~ /^$/);
  		
  		my $checkSha = "sha1_content";
    	if ($mode =~ /update/i)
    	{
    		$checkSha = "sha1_local";
    	}
    	
		my 	$fileWithSpace 	=  $file;
    	    $fileWithSpace 	=~ s#%20# #g;
    	
    	# check and remove files which are not in destination folder
 		if ( $filesToDownload{$file}{'sha1_art'} eq "")
 		{
 			if ( -f "$dir/$fileWithSpace" ) # check and keep files in content.sha1 if exist in destination folder
 			{
 				my $checksumFile = "$filesToDownload{$file}{'sha1_content'} \*\./$fileWithSpace\n";
    			push (@finalChecksumFileList ,$checksumFile);
 			}
    		delete($filesToDownload{$file});
      		next;
 		}   	
 		
    	if ($filesToDownload{$file}{'sha1_art'} eq $filesToDownload{$file}{$checkSha})  # remove entry from hash, has not to be downloaded
    	{
    		if ( $mode =~ /fast/i && !( -f "$dir/$fileWithSpace" ) ) 
    		{
    			next;
    		}
    		my $checksumFile = "$filesToDownload{$file}{'sha1_art'} \*\./$fileWithSpace\n";
    		push (@finalChecksumFileList ,$checksumFile);
      		delete($filesToDownload{$file});
      		next;
    	}
    	# remove file which are different from artifactory in order to enable download
    	# Caution: Download will not complain about if file exists and cannot be overwritten
    	else
    	{
    		# removes files whose content is different from artifactory
      		unlink("$dir/$fileWithSpace");
    	}
  	}
  	print Dumper \%filesToDownload if $debug ;
}

#################################################################################################################
#Cache remote artifacts if not cached already
#
sub cacheRemoteArtifacts
{
    my $inputfeed = shift;

    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    my $dirname  = dirname($$inputfeed{fileArtifact});
    my $basename = basename($$inputfeed{fileArtifact});
    my $repo     = $$inputfeed{repo};
    my $out_dir = $$inputfeed{outputFolder};
    my $regex = glob_to_regex($basename);
    #$decodedFileList->{'errors'}[0]{'message'}
	
	$cmd .= "-s -S -X GET \"$server/$repo/$dirname/\"";
	my @cache_check_output = `$cmd`;

	unless (grep /errors/i, @cache_check_output)
	{		
		checkCache(\@cache_check_output, $regex); 
		#print Dumper \@file_to_cache;
		if (! -d $out_dir) 
    	{
    		mkpath($out_dir);
    	}
		if ($#file_to_cache >= 0)
		{
			write_complete_log("\nINFO: Some of the folders and files are not cached from remote, download may take more time than usual\n");
			createCache($repo,$dirname,$out_dir,\@file_to_cache);
		}
	}
}

#################################################################################################################
#Create cache if not cached already from remote repository
#
sub createCache
{
	my ($repo, $path, $dir, $cache_file) = @_;
	$dir =~ tr|\\|/|;
	my ($cached_file_count, $error_file_count) = (0, 0);
	
  	foreach my $file (@$cache_file)
  	{
  		my $temp = $file;
  		$temp =~ s/%20/ /g;
		
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
		# [Incident: 2132936]
        # $cmd .= "-s -S -X GET \"$server/$repo/$path/$file\" -o \"$dir/$temp\" --write-out \"%{http_code}\"";
		$cmd .= "-X GET \"$server/$repo/$path/$file\" -o \"$dir/$temp\" ";
		my @create_cache_output = `$cmd`;
		
		if ($? eq "0") 
		{	
			$cached_file_count++;
			write_complete_log("$repo/$path/$file - @create_cache_output - OK\n", $verboseMode);
		}
		else
		{
			$error_file_count++;
			write_complete_log("$repo/$path/$file - @create_cache_output - ERROR\n", $verboseMode);
			$errorString .= "ERROR during caching: $path/$file\n";			
		}
  	}
  	
  	write_complete_log("\nINFO: Number of files cached - $cached_file_count, Number of files not cached - $error_file_count\n");
}

#################################################################################################################
#Check for file cache from remote repository
#
sub checkCache
{
	my ($cachedoutput, $files_to_include) = @_;

	foreach my $line (@$cachedoutput)
	{
		next if ($line =~ '<a href="../">../</a>');
		next unless ($line =~ '<a href=');

		if($line =~ /<a href=\"(.*)".*->/ )
		{
			my $match_file = $1;
			$match_file =~ s#\s+#%20#g;
			next if ($match_file =~ /sha1$/);
			next if ($match_file =~ /md5$/);

  			if ( $match_file =~ $files_to_include )
  			{
  				push (@file_to_cache, $match_file);
  			}
		}
	}
}
