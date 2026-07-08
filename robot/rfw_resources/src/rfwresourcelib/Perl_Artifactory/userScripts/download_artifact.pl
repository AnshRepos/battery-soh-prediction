#################################################################################################################################################################################
#																																												#
# FILE			: download_artifact.pl																																			#
#																																												#
# DESCRIPTION	: Download a specified version of component from artifactory repository																							#
#																																												#
# USAGE			: download_artifact.pl  [ -h ] ( -m | -d ) -f <configFile>| -r repo -o <outputFolder> ( -c <component>|( -g <groupId> -a <artifactId> -v <version>)) 			#
#										[ -verbose ] [ -mode <fast|update|complete>] [ -s <server> -u <userId> -p <password> -useproxy]                                         #
#																																												#
# ARGUMENTS		: see Usage																																						#
#																																												#
# COPYRIGHT		: (c) 2014 Robert Bosch GmbH																																	#
# HISTORY		:																																								#
#																																												#
# Date         	| Author                 		| Modification																													#
# 23.10.2014   	| M.Schoenfelder (ext)   		| Initial version																												#
# 07.11.2014   	| M.Schoenfelder (ext)   		| User and pwd of config_file can be overwritten by arguments																	#
#              	                           		  error message if user and pwd not set																							#
# 22.06.2015   	| M.Schoenfelder (ext)   		| adapt to new config file for server, user and pwd info																		#
# 14.07.2015   	| M.Schoenfelder (ext)   		| use 'http:' in file info check, server name can be exchanged internally														#
# 10.09.2015   	| M.Schoenfelder (ext)   		| download only if file does not exist or verification of checksum not ok														#
# 05.11.2015   	| Saddam hussain. A (RBEI/ECA2) | Complete download bug fix,																									#
#                                         		  Adaption to maven and generic repository(can download maven and generic repository artifacts) : Story-43040, 					#
#                                         		  Added log files for complete download files, errro files, download count, error count,time taken to download : Story-43691,	#
#                                         		  Remote repository files autocache before download operation if not cached already : Story-44579,								#
#                                         		  Appropriate Error message display handling : Story-43685,																		#
#                                         		  Space handling in files and folder during upload(can upload files and folder with space) : Story-43685,						#
#                                         		  Empty directory download(Can download empty folder) : Story-43685,															#
#                                         		  Extra input arguments handling(Exit if any anonymous input arguments passed) : Story-44832,									#
#                                          		  User permission check before upload : Story-44168.																			#
# 10.12.2015   	| Saddam Hussain. A (RBEI/ECA2)	| Update download mode added : Story-44832,																						#
#												  Permission check before reading .artfiactory,config file and reading,creating output folder : Story-44832,					#
#												  JSON decoder used to parse json output from artifactory rest api : Story-44832.												#
# 01.03.2016	| Saddam hussain A 	(RBEI/ECA2)	| Adapt to new config file ( check settings, normalise path function)	: story-52827											#
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled windows based execution : feature-76330                                                                               #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled verbose mode and progress bar: feature-76327                                                                          #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled mac based execution : feature-76330                                                                                   #
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		| Modified code to handle empty line with spaces in config file					 												#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | Made modifications to write the full repository path in log file and added latest script version check functionality-			#
#												  story-165111																													#
# 05.09.2017	| Sounak Patra (RBEI/ECA2)		| Added option to generate file to store md5 values: story-178336								 								#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		| Added feature to stop execution of older scripts: story-185699																#
# 20.12.2017	| Sounak Patra (RBEI/ECA2)		| Improved error handling, logging for caching files in remote repository and md5 checksum validation: story-222017				#
# 20.12.2017	| Sounak Patra (RBEI/ECA2)		| Fixed path issue for caching data in Linux OS																					#
# 15.03.2019	| Sounak Patra (RBEI/ECQ2)		| Added noproxy option in curl                                                                                                  #
# 04.09.2019	| Sounak Patra (RBEI/ECQ2)		| Added fix for remote repository caching issue                                                                                 #
# 06.09.2019	| Sounak Patra (RBEI/ECQ2)		| Added error handling during caching files                                                                                     #
#                                                                                                                                                                               #
#################################################################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use File::Path;
use Getopt::Long;
use Data::Dumper;
use JSON qw( decode_json );
use Cwd;
use Cwd qw( abs_path );

# Usage
my $usage = 
{
	'header'	=>	'Usage:',
	'prefix_arguments' => "perl $0",
	'all_arguments' => ' [ -h ] ( -m | -d ) -f <configFile>| -r repo -o <outputFolder> ( -c <component>|( -g <groupId> -a <artifactId> -v <version>)) [ -verbose ] [-generatemd5] [ -mode <fast|update|complete>] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'maven_arguments' => ' -m -f <configFile>| -r repo -o <outputFolder> -g <groupId> -a <artifactId> -v <version> [ -verbose ] [-generatemd5] [ -mode <fast|update|complete>] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'generic_arguments'=> ' -d -f <configFile>| -r repo -o <outputFolder> -c <component> [ -verbose ] [-generatemd5] [ -mode <fast|update|complete>] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'content' => 'Download a specified version of component from artifactory repository.',

	'description' =>
		{  
			'1' => {	'-h' =>  '-h                           : Print this usage text.',},
    		'2' => {	'-m' =>  '-m <maven>                   : For maven repository layout',},
    		'3' => {	'-d' =>  '-d <generic>                 : For generic repository layout'},
    		'4' => {    '-f' =>  '-f <configFile>              : Configuration file with all argument information'},
    		'5' => {	'-r' =>  '-r <repo>                    : Artifactory repository, cannot be used with -f'},
    		'6' => {	'-o' =>  '-o <outputFolder>            : Output folder, cannot be used with -f'},
    		'7' => {	'-c' =>  '-c <component>               : Component (full path inside repository to fetch artifacts), cannot be used with -f'},
    		'8' => {	'-g' =>  '-g <groupId>                 : GroupId, use together with -a'},
    		'9' => {	'-a' =>  '-a <artifactId>              : ArtifactId, use together with -g'},
    		'10'=> {	'-v' =>  '-v <version>                 : Version of an artifact, cannot be used with -f'},
    		'11'=> {	'-verbose' =>  '-verbose                     : Verbose mode'},
    		'12'=> {	'-generatemd5' =>  '-generatemd5             : Generates _content.md5 file'},
    		'13'=> {'-mode'  =>  '-mode <fast|update|complete> : Mode to check existing files before downloading:
				       fast	- default: download the missing/deleted files in the output folder. 
				                  Script does not check for file content change in the output folder.
				                  The existent files in output folder will not be deleted, if those file are not available in repository. 
				       update	- update the output folder with changed/deleted files. 
				                  The existent files in output folder will not be deleted, if those file are not available in repository.  
				       complete	- same behavior as update, but it deletes the files from output folder which does not exist in repository. 
				                  Low performance, use this option when fresh update required.'},
    		'14'=> {	'-s' =>  '-s <server>                  : Artifactory Server (optional, will override config file)'},
    		'15'=> {	'-u' =>  '-u <userId>                  : Artifactory User ID (optional, will override config file)'},
    		'16'=> {	'-p' =>  '-p <password>                : Artifactory Password (optional, will override config file)'},
    		'17'=> {	'-useproxy' =>  '-useproxy                    : Uses current proxy settings (optional, will override config file)'}
		},
    'end_content' => 'Format of <configFile>:
				# used with comments
				# one line per download; items seperated by two colon; all arguments are mandatory
				Repository::outputFolder::component if generic repository
				Repository::outputFolder::groupId::artifactId::version if maven repository
       	
				When using optional arguments like server, userId, password the settings from .artifactory config file will be overwritten!',
};

# arguments
my ( $server, $userId, $password, $verboseMode, $generatemd5, $repository_name, $no_proxy);
my @argument_list 	= ();
my $mode        	= "fast";
my $maven			= 0;
my $generic			= 0;

# other vars
my $auto_answer   				= $ENV{_SET_ENV_AUTO_ANSWER};
my $start_time					= time();
my $end_time					= 0;
my $downloaded_file_count		= 0;
my $file_to_download_count		= 0;
my $error_download_file_count	= 0;
my $failed_validation_file_count   = 0;
my $debug       				= 0;
my %files       				= ();   # list of files with checksum info (art, local, from existing _content file)
my @final_checksum_file_list	= ();
my @file_to_cache 				= ();
my @dir_to_cache 				= ();
my $error_string 				= "";
my $dev_nul 					= "/dev/null";
my $download_log_file       	= 'download.log';
my $error_log_file		   		= 'download_error.log';


# Create log file
my $artifactoryLogDir = create_log_file( $download_log_file, $error_log_file );
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
write_error_log("On Server\t: $server\n");

CONFIG:	
	my $version_count = 0;
	print "\n";	
	foreach my $input_feed_href (@argument_list) 
	{
		$version_count ++;
		%files       				= ();   # resetting all content for each download through config
		@final_checksum_file_list	= ();
		@file_to_cache 				= ();
		@dir_to_cache 				= ();
		
		# Exit if server is not pingable or given repository not found
		if( check_settings( $server, $userId, $password, $$input_feed_href{repo}, $no_proxy)) 					# source repository existence check
		{
			my 	$writeString			= "\nERROR: Source repository not found or user not having read permission to ";
				$writeString 	       .= "repository: $$input_feed_href{repo} in artifactory server: $server\n\n";
		   	write_error_log($writeString);
		   	$error_string              .= $writeString;
		   	next CONFIG;
		}
  		
  		# create output_folder if not existent, check for user permissions
  		write_complete_log("\n--------- Processing $$input_feed_href{output_folder}... ---------\n", $verboseMode);
  		if (! -d $$input_feed_href{output_folder}) 
  		{
			my $parentPath = dirname( $$input_feed_href{output_folder} );
    		while ( ! -d $parentPath ) 
    		{
    			#print "trying to create path \n";
      			$parentPath = dirname($parentPath);
   			}
    		# check if folder is writeable by user
    		if( -w $parentPath )
  			{
  				eval { mkpath( $$input_feed_href{output_folder} ) };
				if ($@)
				{
					write_error_log("\nERROR: Not able to create path $$input_feed_href{output_folder}, Message: $!\n\n", $verboseMode);
					write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  					exit(1);
				}
				else
				{
					write_complete_log("INFO: Output folder not exist, Created..\n", $verboseMode);
				}
  			}
  			else
  			{
  				write_error_log("\nERROR: Output folder: $$input_feed_href{output_folder} not exist, User not having permission to create it.\n", $verboseMode);
  				write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  				exit(1);
  			}
  		}
  		else
  		{
  			if ( ! -w $$input_feed_href{output_folder} )
  			{
  				write_error_log("\nERROR: Output folder: $$input_feed_href{output_folder} exist, User not having write permission to perform download.\n", $verboseMode);
  				write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  				exit(1);
  			}
  			else
  			{
  				write_complete_log("INFO: Output folder exist, Proceeding...\n", $verboseMode);
  			}
  		}

  		# get repository configuration to check it is a remote repository or includes remote repository incase virtual repository (will be added later)
  		#my $repo_config_check_response = getRepoConfig($$input_feed_href{repo});
  		
  		# create remote artifacts cache if not cached
  		cacheRemoteArtifacts($input_feed_href) ; #if ($repo_config_check_response);
  		
  		my $write_string	= "";
  	   	   $write_string    = "\nDownloading from $$input_feed_href{repo}/$$input_feed_href{component}/$$input_feed_href{version} to $$input_feed_href{output_folder}...\n";
  	       $write_string   .= "Operation(mode)    : download(fast)\n\n"       if  ($mode =~ /fast/i);
  	       $write_string   .= "Operation(mode)    : download(update)\n\n"     if  ($mode =~ /update/i);
  	       $write_string   .= "Operation(mode)    : download(complete)\n\n"   if  ($mode =~ /complete/i);
		write_error_log($write_string, $verboseMode);
		
  		my $response = get_file_list(%{$input_feed_href});
  		next CONFIG if ($response);

  		# not first download, evaluate checksums and change files list for download accordingly
  		if (-f $$input_feed_href{output_folder}."/_content.sha1") 
  		{
    		# create local checksum file if requested
    		if ($mode =~ /(complete|update)/i) 
    		{
      			if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i){
      				createLocalChecksumFileLinux($$input_feed_href{output_folder})
      			}
      			elsif ($^O =~ /mswin/i){
      				createLocalChecksumFileMswin($$input_feed_href{output_folder})
      			}
    		}
    		else
    		{
    			fillContentSha($$input_feed_href{output_folder}."/_content.sha1");
    		}
    		print Dumper(\%files) if ($debug);
    		diffChecksums($$input_feed_href{output_folder});
    
    		# remove old file before renaming new created artifactory checksum file
    		rename($$input_feed_href{output_folder}."/_content.sha1",$$input_feed_href{output_folder}."/_content.sha1.keep");
  		} 
  
  		# download files according to %files
  		download($input_feed_href, $version_count, scalar @argument_list);
	}
	print "\n";

# Calculate time to complete download
$end_time 		= time();
my $duration 	= $end_time - $start_time;
my $minutes 	= int ( ( $duration / 60 ) % 60 );
my $seconds 	= $duration % 60;
my $hours 		= int( ( $duration /60) / 60 );

# Check for intermediate errors and exit
if ($error_string ne "") 
{
	my $write_string = "";
  	   $write_string .= "\nFollowing problems occured during script execution:\n";
  	   $write_string .= "-----------------------------------------------------\n";
  	   $write_string .= "$error_string\n\n";
  	write_error_log($write_string);
  	write_error_log("\nTotal no. of files: $file_to_download_count, downloaded: $downloaded_file_count, failed: $error_download_file_count\n");
  	if ($generatemd5 && $failed_validation_file_count != 0)
  	{
  		write_error_log("\nMd5 checksum validation failed for $failed_validation_file_count file/files\n");
  	}
  	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nDownload log       : $artifactoryLogDir$download_log_file\n"; 
	print "Error log          : $artifactoryLogDir$error_log_file\n";
  	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(1);
}
else 
{
	write_error_log("\nTotal no. of files: $file_to_download_count, downloaded: $downloaded_file_count, failed: $error_download_file_count\n");
  	if ($generatemd5 && $failed_validation_file_count != 0)
  	{
  		write_error_log("\nMd5 checksum validation failed for $failed_validation_file_count file/files\n");
  	}
	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nDownload log       : $artifactoryLogDir$download_log_file\n"; 
	print "Error log          : $artifactoryLogDir$error_log_file\n";
	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
  	exit(0);
}

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# get repository configuration to check if it is a remote repository or contains remote repository incase virtual repository
# (Function not used now, will be used in future)
# Example json output:
#"key" : "basesoftware-release",
#"packageType" : "maven",
#"repositories" : [ "test_remote" ],
#"artifactoryRequestsCanRetrieveRemoteArtifacts" : false,
#"keyPair" : "",
#"pomRepositoryReferencesCleanupPolicy" : "discard_active_reference",
#"rclass" : "virtual"
#
sub getRepoConfig
{
	my $repo_to_check 		= shift;
	
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    $cmd .= "-sS -X GET \"$server/api/repositories/$repo_to_check\"";
	my $repo_config_output 	= `$cmd`;
	my $decoded_repo_config = decode_json($repo_config_output);

  	if (defined $decoded_repo_config->{'errors'} ) 
  	{
    	$error_string .= "Not able to get configuration for repository $repo_to_check, download will proceed without checking files are cached from remote\n";
    	write_console("\nNot able to get configuration for repository $repo_to_check, download will proceed without checking files are cached from remote\nError message : $decoded_repo_config->{'errors'}[0]{'message'}\n");
    	return(0);
  	}

 	return(0) if ($decoded_repo_config-> {'rclass'} =~ /^local$/i );
 	
 	if ($decoded_repo_config->{'rclass'} =~ /^virtual$/i )
	{
		if (defined $decoded_repo_config->{'repositories'})
		{
			foreach (@{$decoded_repo_config->{'repositories'}})
			{
				my $response = getRepoConfig($_);
				return(1) if $response;
			}
		}
	}
	else
	{
		return(1);
	}
}

#################################################################################################################
#Check for version cache recursively from version (recursively check for cache under version and its folder) : Story-44579
#
sub checkCacheRecursive
{
	my ($inputfeed,$dir_to_check) = @_;
	chomp ($dir_to_check);
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);

	if ($maven){
		$cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$dir_to_check/\""
	}
	elsif ($generic){
		$cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/$dir_to_check/\""
	}
	my @recursive_cache_check_output = `$cmd`;
	unless (grep /errors/i, @recursive_cache_check_output)
	{		checkCache($inputfeed,\@recursive_cache_check_output,$dir_to_check); }
}

#################################################################################################################
#Check for version cache from remote repository(check incase downloading from virtual repository including remote repository artifacts are cached) : Story-44579
#List view of files and folder under version, if cached will show size and modified date else will show dash for modified date and size and in the end of the href will have ->
#
#<pre>Name                        Last modified      Size</pre><hr/>
#<pre><a href="../">../</a>
#<a href="deploy/">deploy/</a>                      31-Oct-2015 15:12    -
#<a href="deploy1/">deploy1/</a>                     31-Oct-2015 15:12    -
#<a href="hello/">hello/</a>                       31-Oct-2015 15:12    -
#<a href="New folder/">New folder/</a>->                    -    -
#<a href="test/">test/</a>                        31-Oct-2015 15:12    -
#<a href="a-2.0.pom">a-2.0.pom</a>->                      -    -
#<a href="a-2.0.pom.md5">a-2.0.pom.md5</a>->                  -    -
#<a href="a-2.0.pom.sha1">a-2.0.pom.sha1</a>->                 -    -
#<a href="New Text Document.txt">New Text Document.txt</a>->          -    -
#<a href="New Text Document.txt.md5">New Text Document.txt.md5</a>->      -    -
#<a href="New Text Document.txt.sha1">New Text Document.txt.sha1</a>->     -    -
#<a href="new_overwrite.txt">new_overwrite.txt</a>            30-Oct-2015 19:36  15 bytes
#
sub checkCache
{
	my ($inputfeed,$cachedoutput,$dir_to_include) 	= @_;
	my $out_dir;
	foreach my $line (@$cachedoutput)
	{
		# next if ($line =~ '<a href="../">../</a>');
		# next unless ($line =~ '<a href=');
        if ($line =~ '<a href=')
        {
            # trimming leading and trailing spaces
            $line =~ s/^\s+|\s+$//g;
            if ($line eq '<pre><a href="../">../</a>' || $line eq '<a href="../">../</a>')
            {
                next;
            }                      				
        }

		if($line =~ "<a href=\"(.*)\/\">(.*)\/<\/a>" )
		{
			my $match_dir = $1;
			$match_dir =~ s#\s+#%20#g;
			if ($dir_to_include)
			{
				$out_dir = $$inputfeed{output_folder}."/"."$dir_to_include\/$match_dir";
				checkCacheRecursive($inputfeed,"$dir_to_include\/$match_dir");
			}
			else
			{
				$out_dir = $$inputfeed{output_folder}."/".$match_dir;
				checkCacheRecursive($inputfeed,$match_dir);
			}
			# create directory structure if not there in local output folder
			$out_dir =~ s/%20/ /g;
			if (! -d $out_dir) 
    		{
    			mkpath($out_dir);
    		}
			next;
		}
		
		if($line =~ /<a href=\"(.*)".*->/ )
		{
			my $match_file = $1;
			$match_file =~ s#\s+#%20#g;
			next if ($match_file =~ /sha1$/);
			next if ($match_file =~ /md5$/);
			if ($dir_to_include)
			{
				push (@file_to_cache,"$dir_to_include\/$match_file");
			}
			else
			{
				push (@file_to_cache,$match_file);
			}
		}
	}
}

#################################################################################################################
#Cache remote artifacts if not cached already (check incase downloading from virtual repository including remote repository artifacts are cached)  : Story-44579
#
sub cacheRemoteArtifacts
{
	my $inputfeed = shift;
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);

	if ($maven){
		$cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/\""
	}
	elsif ($generic){
		$cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/\""
	}
	my @cache_check_output = `$cmd`;

	unless (grep /errors/i, @cache_check_output)
	{		
		checkCache($inputfeed,\@cache_check_output); 
		if ($#file_to_cache >= 0)
		{
			write_complete_log("\nINFO: Some of the folders and files are not cached from remote, download may take more time than usual\n");
			createCache($inputfeed,\@file_to_cache);
		}
	}
}

#################################################################################################################
#Create cache if not cached already from remote repository  : Story-44579
#
sub createCache
{
	my ($inputfeed,$cache_file) = @_;
	my ($cached_file_count, $error_file_count) = (0, 0);	
	
  	foreach my $file (@$cache_file)
  	{
  		my $temp = $file;
  		$temp =~ s/%20/ /g;
  		my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
  		   $cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\" " if ($maven);
           $cmd .= "-s -X GET \"$server/$$inputfeed{repo}/$$inputfeed{component}/$file\" " if ($generic);
           $cmd .= "-o \"$$inputfeed{output_folder}/$temp\" --write-out \"%{http_code}\"";
		my @create_cache_output = `$cmd`;

		if ($? eq "0") 
		{
            my $error_code_digit = (split //, $create_cache_output[0])[0];
			if ($error_code_digit == 4)
			{
	    		$error_file_count++;
				if ($maven)
				{
                    write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file - @create_cache_output - ERROR\n", $verboseMode);
                    write_error_log("$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file - @create_cache_output - ERROR\n", $verboseMode);
                    $error_string .= "ERROR during caching: $$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\n";
				}
				else
				{
                    write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$file - @create_cache_output - ERROR\n", $verboseMode);
                    write_error_log("$$inputfeed{repo}/$$inputfeed{component}/$file - @create_cache_output - ERROR\n", $verboseMode);
                    $error_string .= "ERROR during caching: $$inputfeed{repo}/$$inputfeed{component}/$file\n";
				}
			}
            else
            {
                $cached_file_count++;
                if ($maven)
                {
                    write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file - @create_cache_output - OK\n", $verboseMode);
                }
                else
                {
                    write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$file - @create_cache_output - OK\n", $verboseMode);
                }
            }
		}
		else
		{
			$error_file_count++;
			if ($maven)
			{
				write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file - @create_cache_output - ERROR\n", $verboseMode);
				$error_string .= "ERROR during caching: $$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\n";
			}
			else
			{
				write_complete_log("$$inputfeed{repo}/$$inputfeed{component}/$file - @create_cache_output - ERROR\n", $verboseMode);
				$error_string .= "ERROR during caching: $$inputfeed{repo}/$$inputfeed{component}/$file\n";
			}						
		}
  	}
  	
    write_complete_log("\nINFO: Number of files cached - $cached_file_count, Number of files not cached - $error_file_count");
  	write_complete_log("\nINFO: Please check log files for errors");
}

#################################################################################################################
# get file list for version from artifactory : Story-44832 (Used JSON decoder to parse output from rest api)
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
sub get_file_list
{
	my %inputfeed = @_;
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
	$cmd .=  "-X GET --silent -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.FileList+json\" ";

	if ($maven){
		$cmd .= "\"$server/api/storage/$inputfeed{repo}/$inputfeed{component}/$inputfeed{version}?list&deep=1&listFolders=1&mdTimestamps=1\""
	}
	elsif ($generic){
		$cmd .= "\"$server/api/storage/$inputfeed{repo}/$inputfeed{component}?list&deep=1&listFolders=1&mdTimestamps=1\""
	}
    my $filelist_json = `$cmd`;
	
    my $decoded_filelist = decode_json($filelist_json);
	
  	if (defined $decoded_filelist->{'errors'} ) 
  	{
    	$error_string .= "No download of $inputfeed{component}/$inputfeed{version} possible:\n";
    	write_console("\nError message : $decoded_filelist->{'errors'}[0]{'message'}\n");
    	return(1);
  	}
  	
  	my @folder_file_list = @{$decoded_filelist->{'files'}};
    for (my $i=0;$i<=$#folder_file_list;$i++) 
  	{
  		#check for files
  		if ($folder_file_list[$i]{'folder'} == 0 )
  		{  			
  			my 	$filename = $folder_file_list[$i]{'uri'};
  				$filename =~ s#^\/##;  				
  				$files{$filename}{sha1_art} = $folder_file_list[$i]{'sha1'};	
  		}
  		#check for folders
  		elsif ($folder_file_list[$i]{'folder'} == 1)
  		{
  			my 	$out_dir = $inputfeed{output_folder}.$folder_file_list[$i]{'uri'};
  				$out_dir =~ s/%20/ /g;
    			mkpath ($out_dir) if (! -d $out_dir); 
  		}
  		else 
      	{
       		$error_string .= "Could not evaluate type (dir/file) of $folder_file_list[$i]{'uri'}\n";
      	}
  	}
  	return(0);
}

#################################################################################################################
# fill array content_sha will info from sha_file (without line feed)
#
sub fillContentSha
{
  	my $sha_file  	= shift;
  	my $src_folder 	= dirname($sha_file);
  	my @local_files;
  	open(SHA, "<$sha_file") or die "Could not open $sha_file for reading\n\n===========================================================================================================\n\n";
  	
	# get current present files from local  
#	@local_files = createLocalChecksumFileLinux($src_folder) if ($^O =~ /linux/i || $^O =~ /cygwin/i);
#	@local_files = createLocalChecksumFileMswin($src_folder) if ($^O =~ /mswin/i);
    if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i){
    	@local_files = createLocalChecksumFileLinux($src_folder)
    }
    elsif ($^O =~ /mswin/i){
    	@local_files = createLocalChecksumFileMswin($src_folder)
    }
    
  	while(my $line=<SHA>)
  	{
  	  	$line =~ s/[\r\n]//g;
    	my ($sha1,$file) = split(/\s*\*\.\//,$line);
    	foreach (@local_files) 
    	{
       		#if(grep /^$file/, @local_files)
       		if ($file eq $_)
    		{
    			$files{$file}{sha1_content} = $sha1;
    			last;
       		}
    	}
  	}
  	close(SHA);
}

#################################################################################################################
# create checksum file read from local files and fill values of sha_local
#
sub createLocalChecksumFileLinux
{
  	my $dir = shift;
  	my $sha_file .= $dir."/_content.sha1.local";
  	if ($mode =~ /(complete|update)/i)
  	{
  		open(SHASUM, ">$sha_file") or die "Could not open $sha_file\n\n===========================================================================================================\n\n";
#  		my $cmd = "find $dir -type f -print0 |xargs -0 sha1sum";
		my $cmd = "";
  		if ($^O =~ /darwin/i){
  			$cmd = "find $dir -type f -print0 |xargs -0 shasum"
  		}
  		else{
  			$cmd = "find $dir -type f -print0 |xargs -0 sha1sum"
  		}
  		my @local_file_list_output = `$cmd`;
  		foreach my $line (@local_file_list_output) 
  		{
    		next if ($line =~ /^(\.|\.\.)$/);		  # do not include hidden files 
    		next if ($line =~ /_content.sha1/);   # do not include checksum files
    		$line =~ s#\Q$dir\E#\*\.#;
    		print SHASUM $line;
    		$line =~ s#[\r\n]##g;
    		my ($sha1,$file) = split(/\s*\*\.\//,$line);
    		$files{$file}{sha1_local} = $sha1;
  		}	
  		close(SHASUM);
  	}
  	else
  	{
  		my @local_files_linux;
  		my $cmd = "find $dir -type f";
  		my @local_file_list_output = `$cmd`;
  		foreach my $line (@local_file_list_output) 
  		{
  			#chomp($line);
    		next if ($line =~ /^(\.|\.\.)$/);		  # do not include hidden files 
    		next if ($line =~ /_content.sha1/);   # do not include checksum files
    		$line =~ s#\Q$dir\E/##;
    		$line =~ s#[\r\n]##g;
    		push (@local_files_linux, $line);
    	}	
  		return (@local_files_linux);
  	}
}

#################################################################################################################
# create checksum file read from local files and fill values of sha_local
#
sub createLocalChecksumFileMswin
{
  	my $dir 		= shift;
  	my $dir_win 	= $dir;
       $dir_win 	=~ s#\/#\\#g;
  	my $sha_file   .= $dir."\\_content.sha1.local";
  	my $cmd 		= 'dir /B /S';
  	my @local_file_list_output = `$cmd "$dir_win" 2>nul`;

  	if ($mode =~ /(complete|update)/i)
  	{
  		$dir =~ tr|/|\\|;
  		open(SHASUM, ">$sha_file") or die "Could not open $sha_file\n\n===========================================================================================================\n\n";
  		foreach my $line (@local_file_list_output) 
  		{
    		chomp($line);
    		next if ($line =~ /_content.sha1/);   # do not include checksum files
    		if (-f $line) 
    		{
				my $sha1 = get_hash_value('SHA1', $line);			
				substr($line, index($line, $dir), length($dir)) = "";
				$line =~ tr|\\|/|;
				print SHASUM "$sha1". " *.". "$line\n";
				my $file = substr($line, 1);				
    	  		$files{$file}{sha1_local} = $sha1;
    	  	}
  		}
  		close(SHASUM);
  	}
  	else
  	{
  		my @local_files_mswin;
  		foreach my $line (@local_file_list_output) 
  		{
    		chomp($line);
    		next if ($line =~ /_content.sha1/);   # do not include checksum files
    		if (-f $line) 
    		{
    			$line =~ s#^\\\\#\\\\\\\\#;
    	  		$line =~ s#\\\\#\\#g;
    	  		$line =~ s#(\w:)?\Q$dir_win\E\\##;
    	  		$line =~ s#\\#/#g;
    	  		$line =~ s#[\r\n]##g;
			    push (@local_files_mswin, $line);
    	  	}
  		}
  		return(@local_files_mswin);
  	}
}

#################################################################################################################
# diff checksum files
#
sub diffChecksums
{
  	my $dir = shift;
  	my $temp = scalar keys (%files);
  	foreach my $file (keys(%files)) 
  	{
  		
  		next if ($file =~ /^$/);
    	# file not in artifactory -> should be removed, remove hash entry
    	if ($files{$file}{sha1_art} eq "") 
    	{
      		#write_complete_log("File is not in artifactory, should probably be removed: $file\n");
		my $checksum_file = "$files{$file}{sha1_content} \*\./$file\n";
      		delete($files{$file});      		
      		# Removes files which are not there in artifactory
      		if (($mode =~ /complete/i))
      		{
      			# Caution: download will not complain if file in use and not able to delete
	      		if ($file ne "_content.md5")
	      		{
	       			unlink("$dir/$file");
	       			write_complete_log("File is not in artifactory, will be removed from local: $file\n", $verboseMode);    			
	      		}
	      		else
	      		{
	      			write_complete_log("File is not in artifactory: $file\n", $verboseMode);
	      		}
      		}
      		else
      		{
    			push (@final_checksum_file_list ,$checksum_file);
      			write_complete_log("File is not in artifactory, should probably be removed: $file\n", $verboseMode);
      		}
      		next;
    	}
    	my $check_sha = "sha1_content";
    	if ($mode =~ /(complete|update)/i) {$check_sha = "sha1_local";}
    	if ($files{$file}{sha1_art} eq $files{$file}{$check_sha})  # remove entry from hash, has not to be downloaded
    	{
    		my 	$file_with_space 	=  $file;
    			$file_with_space 	=~ s/%20/ /g;
    		my $checksum_file = "$files{$file_with_space}{sha1_art} \*\./$file_with_space\n";
    		push (@final_checksum_file_list ,$checksum_file);
      		delete($files{$file});
      		next;
    	}
    	# remove file which are different from artifactory in order to enable download
    	# Caution: Download will not complain about if file exists and cannot be overwritten
    	else
    	{
    		# removes files whose content is different from artifactory
      		unlink("$dir/$file");
    	}
  	}
}

#################################################################################################################
# download files, no further checksum check necessary, array @files only contains files to be downloaded
# check has been taken place before calling download
#
sub download
{
  	my $inputfeed    					= shift;
  	my $version_count					= shift;
  	my $total_no_of_versions 			= shift;
  	my $file_with_space 				= "";
  	my @file_to_remove_from_content_sha = ();
  	$file_to_download_count 		   += scalar keys(%files);
  	my $file_count						= scalar keys(%files);
	my $file_download_progress			= 0;
	my @md5_file_list;
	my @md5_error_list;

  	my $def_percentage_counter = 0;
  	   $def_percentage_counter = (100 / scalar(keys(%files))) if (scalar(keys(%files)));
    
  	foreach my $file (keys(%files)) 
  	{
  		$file_download_progress++;
    	chomp($file);
    	my $download_progress	= "($file_download_progress\/$file_count)";
    	$file_with_space = $file;
    	$file =~ s#\s+#%20#g;
		
		if ($maven)
		{
			write_complete_log("$download_progress .../$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file - ", $verboseMode);
		}
		else
		{
			write_complete_log("$download_progress .../$$inputfeed{repo}/$$inputfeed{component}/$file - ", $verboseMode);
		}

    	# could be done anonymous but user and pwd info used for file-list
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    	   $cmd .= "-sS -f -L --write-out \"%{http_code}\" ";
    	   $cmd .= "\"$server/$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\" " if ($maven); 
    	   $cmd .= "\"$server/$$inputfeed{repo}/$$inputfeed{component}/$file\" " if ($generic); 
    	   $cmd .= "-o \"$$inputfeed{output_folder}/$file_with_space\"";
    	
    	my $result = `$cmd`;
    	if($? eq "0") 
    	{
			my $digit = (split //, $result)[0];
			if ($digit == 4)
			{
	    		write_complete_log("$result - ERROR\n", $verboseMode);
	    		$error_download_file_count++;
				if ($maven)
				{
					$error_string .= "ERROR download: /$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\n";
				}
				else
				{
					$error_string .= "ERROR download: /$$inputfeed{repo}/$$inputfeed{component}/$file\n";
				}
			}
			else
			{
	    		write_complete_log("$result - ok\n", $verboseMode);
	    		my $checksum_file = "$files{$file_with_space}{sha1_art} \*\./$file_with_space\n";    		
	    		push (@final_checksum_file_list,$checksum_file);
	    		$downloaded_file_count++;
	
	    		if (($generatemd5) && (-e "$$inputfeed{output_folder}/$file_with_space"))
	    		{
		    		my $md5_value_local = get_hash_value('MD5', "$$inputfeed{output_folder}/$file_with_space");
		    		my $md5_value_server = "";
		    		if ($maven)
		    		{
		    			$md5_value_server = get_server_generated_md5_checksum_value($server, $userId, $password, $no_proxy, $$inputfeed{repo}, "$$inputfeed{component}/$$inputfeed{version}/$file");
		    		}
		    		else
		    		{
		    			$md5_value_server = get_server_generated_md5_checksum_value($server, $userId, $password, $no_proxy, $$inputfeed{repo}, "$$inputfeed{component}/$file");
		    		}
					if ($md5_value_local ne $md5_value_server)
					{
						push(@md5_error_list, $md5_value_local . " " . $md5_value_server . " *./" . $file_with_space . "\n");
					}		    		
		    		my $md5_content = $md5_value_local . " *./" . $file_with_space . "\n";
		    		push (@md5_file_list, $md5_content);    			
	    		}
			}
    	}
    	else 
    	{
    		write_complete_log("$result - ERROR\n", $verboseMode);
    		$error_download_file_count++;
    		#push (@file_to_remove_from_content_sha,$file);

			if ($maven)
			{
				$error_string .= "ERROR download: /$$inputfeed{repo}/$$inputfeed{component}/$$inputfeed{version}/$file\n";
			}
			else
			{
				$error_string .= "ERROR download: /$$inputfeed{repo}/$$inputfeed{component}/$file\n";
			}
    	}
    	get_progress_percentage(int($def_percentage_counter * $file_download_progress), "Download", $total_no_of_versions, $version_count) if (not $verboseMode);
    }
  	# Write successfully downloaded files and checksums to the content.sha1 file
  	my $content_sha1_file = "$$inputfeed{output_folder}/_content.sha1";
	# Writes SHA1 value to _content.sha1_file
  	write_to_file($content_sha1_file, @final_checksum_file_list);

  	# Writes MD5 value to _content_md5_file
  	if ($generatemd5)
  	{
  		my $content_md5_file = "$$inputfeed{output_folder}/_content.md5";
  		my $content_md5_error_file = "$$inputfeed{output_folder}/_content_error.md5";
	  	my @file_names = keys %files;
	  	generate_md5_file(\@md5_file_list, \@file_names, $content_md5_file);
	  	generate_md5_error_file(\@md5_error_list, $content_md5_error_file);
	  	$failed_validation_file_count += scalar @md5_error_list;
  	}
}

#################################################################################################################
#Display appropriate usage message based on the arguments(all_arguments, maven_arguments, generic_arguments) : Story-43685 (Space handling in files)
#Example output for maven download, here only arguments related to maven donwload is displayed in maven usage
#Usage:
#        perl download_artifact.pl  -m -f <config_file>| -r repo -o <output_dir> -g <group_id> -a <artifact_id> -v <version> [ -mode <fast|update|complete>] [ -s <server>] [ -u <usr_id> -p <pwd>]
#
#        Download a specified version of component from artifactory repository.
#
#        -m <maven>           			: Maven repository download
#        -r <repo>            			: Artifactory Repository, cannot be used with -f
#        -o <output_dir>      			: Output folder (full path), cannot be used with -f
#        -g <group_id>        			: GroupId, use together with -a
#        -a <artifact_id>        	    : ArtifactoryId, use together with -g
#        -v <version>         			: Version of component, cannot be used with -f
#        -mode <fast|update|complete>	: Mode to check existing files before downloading:
#                               		  fast     - default: new checksum file from artifactory will be compared against existing one, without creating checksums from local files
#										  update   - first create new checksum file with loacl checksums, then compare to those from artifactory but will not delete files from local if not in artifactory
#										  complete - first create new checksum file with loacl checksums, then compare to those from artifactory and delete files from local if not in artifactory
#        -s <server>          			: Artifactory Server (optional, will be read from config file)
#        -u <usr_id>          			: Artifactory User ID (optional, will be read from config file)
#        -p <pwd>             			: Artifactory Password (optional, will be read from config file)
#
sub displayUsage
{
	my 	$argument_select 	= shift;
		$argument_select 	= 'all_arguments' unless (defined $argument_select);           						#if maven_arguments, displays only maven usage
    my 	$write_string 		= "$$usage{'header'}\n";															#if generic_arguments, displays only generic usage
		$write_string 	   .= "\t$$usage{prefix_arguments} $$usage{$argument_select}\n";
		$write_string  	   .= "\n\t$$usage{content}\n\n";
	foreach my $description_key (sort {$a <=> $b} keys %{$$usage{description}})
	{
		my @description_inner_key = keys %{$$usage{description}{$description_key}};
		if ($$usage{$argument_select} =~ /\s$description_inner_key[0]\s/)
		{
			$write_string .= "\t$$usage{description}{$description_key}{$description_inner_key[0]}\n";
		}
	}
	$write_string .= "\n\t$$usage{end_content}\n\n";
	write_console($write_string);
}

#################################################################################################################
# scan arguments and assign them to global script variables : Story-43685 (Appropriate error message display for maven and generic),Story-44832(if any anonymous input arguments passed)
# show help text if arguments are not set correctly
#
sub scanArgs
{
  	my (%input_feed, $h, $useproxy, $config_file, $verbose, $generatemd5file);
  
  	my $res = GetOptions (
  		'h'      => \$h,
   		'm'		 => \$maven,
   		'd'		 => \$generic,
   		'u=s'    => \$userId,
   		'p=s'    => \$password,
   		'o=s'    => \$input_feed{output_folder},
   		's=s'    => \$server,
   		'r=s'    => \$input_feed{repo},
   		'c=s'    => \$input_feed{component},
   		'g=s'    => \$input_feed{group_id},
   		'a=s'    => \$input_feed{artifact_id},
   		'v=s'    => \$input_feed{version},
   		'f=s'    => \$config_file,
   		'verbose'    => \$verbose,
   		'generatemd5'    => \$generatemd5file,
        'useproxy'    => \$useproxy,
   		'mode=s' => \$mode,
   		'x'		 => \$debug,						
  		) or do {
  					write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  					displayUsage('all_arguments');
					write_error_log("\n===========================================================================================================\n\n");
					exit(1);
  				}; 

	$repository_name = $input_feed{repo};
	if(scalar @ARGV)
	{
		write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
		displayUsage('all_arguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}
  	if ($h) 
  	{
  		write_error_log("\nINFO: Help message requested!\n");
   		if ($maven || $generic)
  		{
   			($maven) ? 	(displayUsage('maven_arguments')) : displayUsage('generic_arguments');
  		}
  		else
  		{
  			displayUsage('all_arguments');
  		}
   		write_error_log("\n===========================================================================================================\n\n");
    	exit(0);
  	}
  	# maven and generic common arguments check
  	unless ( $maven || $generic)
  	{
		write_error_log("\nERROR: Arguments missing!\nRepository type should be given in the arguments as (-m for maven or -d for generic)\n");
		displayUsage('all_arguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
  	}
  	if ($maven && $generic)
  	{
  		write_error_log("\nERROR: Extra argument, either generic or maven repository can be selected\n");
  		displayUsage('all_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	
  	if (not $verbose){$verboseMode = 0} else {$verboseMode = 1};
  	if (not $generatemd5file){$generatemd5 = 0} else {$generatemd5 = 1};
  	
    if ( !(($mode =~ /^fast$/i) || ($mode =~ /^complete$/i) || ($mode =~ /^update$/i)) ) 
  	{
  		write_error_log("\nERROR: Selected mode is not supported, select fast or update or complete\n");
    	displayUsage('all_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}  	
	if ($config_file) 
  	{ # read infos from file
  	#######################check is need here#########################################  		
    	if ( ($input_feed{output_folder}) || ($input_feed{component}) || ($input_feed{group_id})|| ($input_feed{artifact_id})|| ($input_feed{version}) || ($input_feed{repo})) 
    	{
    		write_complete_log("\nWARNING: Other arguments will be ignored when using -f\n");
    	}
    	# normalise path
  		$config_file = normalise_path($config_file);
  		
  		if ($config_file == 1)
  		{
  			write_error_log("\nERROR: Invalid config file: $config_file path!\n");
  			displayUsage('maven_arguments') 	if ($maven);
			displayUsage('generic_arguments') 	if ($generic);
  			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
  		}
    	if ((! -e $config_file) && (! -f $config_file))
    	{
    		write_error_log("\nERROR: config file: $config_file not exist!\n");
			displayUsage('maven_arguments') 	if ($maven);
			displayUsage('generic_arguments') 	if ($generic);
			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
    	}
    	open(CONFIG, "<$config_file") or die "$config_file cannot be opened!\n\n===========================================================================================================\n\n";
    	my @lines = <CONFIG>;
    	close(CONFIG);
    	
    	if ($maven)
    	{
    		my $line_number = 0;
    		#read each line from config_file to parse input arguments
    		foreach my $line (@lines) 
    		{
    			$line_number++;
      			next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
      			chomp $line;
      			my %input_feed_cfg;
      			my $argument_count;
      			$argument_count = (($input_feed_cfg{repo},$input_feed_cfg{output_folder},$input_feed_cfg{group_id},$input_feed_cfg{artifact_id},$input_feed_cfg{version}) = split(/::/,$line));
      			if ($argument_count > 5)
      			{
      				write_error_log("\nERROR: Extra arguments in config file!\n");
					displayUsage('maven_arguments');
					write_error_log("\n===========================================================================================================\n\n");
  					exit(1);
      			}

      			#remove space before and after the input arguments
				normaliseArguments(\%input_feed_cfg);				
				if (not defined $repository_name)
				{
					$repository_name = $input_feed_cfg{repo};
				}
				
      			# maven arguments check 
      			mavenArgumentCheck(\%input_feed_cfg, $line_number);
      			$input_feed_cfg{component}     		= $input_feed_cfg{group_id}."/".$input_feed_cfg{artifact_id};
    			$input_feed_cfg{component}       	=~ s#\\#/#g;
  				$input_feed_cfg{output_folder}   	= normalise_path($input_feed_cfg{output_folder});
  				if ( $input_feed_cfg{output_folder} == 1 )
	  			{
	  				write_error_log("\nERROR: Invalid Output file: $input_feed_cfg{output_folder} path at line $line_number !\n");
	  				( $maven ) ? ( displayUsage('maven_arguments') ) : ( displayUsage('generic_arguments') );
	  				write_error_log("\n===========================================================================================================\n\n");
	  				exit(1);
	  			}
  				push(@argument_list,\%input_feed_cfg);
    		}
    	}
    	else
    	{
    		my $line_number = 0;
    		foreach my $line (@lines) 
    		{
    			$line_number++;
      			next if ($line =~ /#/  || $line =~ /^$/); 	# ignore comments and empty lines
      			chomp $line;
      			my %input_feed_cfg;
      			my $argument_count;
      			$argument_count = (($input_feed_cfg{repo},$input_feed_cfg{output_folder},$input_feed_cfg{component}) = split(/::/,$line)) ;
      			if ($argument_count > 3)
      			{
      				write_error_log("\nERROR: Extra arguments in config file at line $line_number !\n");
					displayUsage('generic_arguments');
					write_error_log("\n===========================================================================================================\n\n");
  					exit(1);
      			}
      			
      			#remove space before and after the input arguments
				normaliseArguments(\%input_feed_cfg);
				if (not defined $repository_name)
				{
					$repository_name = $input_feed_cfg{repo};
				}				
      			# generic arguments check 
    			genericArgumentCheck(\%input_feed_cfg, $line_number);
    			$input_feed_cfg{component}       =~ s#\\#/#g;
  				$input_feed_cfg{output_folder}   = normalise_path($input_feed_cfg{output_folder});
  			  	if ( $input_feed_cfg{output_folder} == 1 )
	  			{
	  				write_error_log("\nERROR: Invalid Output file: $input_feed_cfg{output_folder} path at line $line_number !\n");
	  				( $maven ) ? ( displayUsage('maven_arguments') ) : ( displayUsage('generic_arguments') );
	  				write_error_log("\n===========================================================================================================\n\n");
	  				exit(1);
	  			}
  				push(@argument_list,\%input_feed_cfg);
    		}
    	}
  	}
  	else 
  	{ 
  		#remove space before and after the input arguments
		normaliseArguments(\%input_feed);
		
  		# arguments check for maven and generic specific     
  		if ($maven)
  		{
  			mavenArgumentCheck(\%input_feed);
  			$input_feed{component}     = $input_feed{group_id}."/".$input_feed{artifact_id};
  		}
  		else
  		{	genericArgumentCheck(\%input_feed); }	
  		
    	$input_feed{output_folder}   = normalise_path($input_feed{output_folder});
    	if ( $input_feed{output_folder} == 1 )
	  	{
	  		write_error_log("\nERROR: Invalid Output file: $input_feed{output_folder} path!\n");
	  		( $maven ) ? ( displayUsage('maven_arguments') ) : ( displayUsage('generic_arguments') );
	  		write_error_log("\n===========================================================================================================\n\n");
	  		exit(1);
	  	}
    	$input_feed{component}       =~ s#\\#/#g;
		push(@argument_list,\%input_feed);
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
# check maven arguments are passed correctly : Story-44832
sub mavenArgumentCheck
{
	my $inputfeed 	= shift;
	my $line_number = shift;

	# missing arguments check
	if ((!$$inputfeed{repo}) || (!$$inputfeed{group_id}) || (!$$inputfeed{artifact_id}) || (!$$inputfeed{version}) || !$$inputfeed{output_folder}) 
  	{
  		my $error_string  = "\nERROR: Arguments ";
  		   $error_string .= '-r <repo>, ' if (!$$inputfeed{repo});
  		   $error_string .= '-g <groupId>, ' if (!$$inputfeed{group_id});
    	   $error_string .= '-a <artifactId>, ' if (!$$inputfeed{artifact_id});
    	   $error_string .= '-v <version>, ' if (!$$inputfeed{version});
    	   $error_string .= '-o <outputFolder>' if (!$$inputfeed{output_folder});
    	   $error_string  =~ s#, $##;

  		($line_number) ? ($error_string .= " missing at line $line_number !\n") : ($error_string .= " missing!\n");
  		write_error_log("$error_string");
    	displayUsage('maven_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# extra arguments check	
  	if ($$inputfeed{component}) 
  	{
  		my $error_string = "\nERROR: Extra -c <component> argument!";
  		($line_number) ? ($error_string .= " at line $line_number !\n") : ($error_string .= " !\n");
  		write_error_log("$error_string");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	# artifact id and version correctness check 
  	if ( ($$inputfeed{artifact_id} =~ /(\\|\/)/) || ($$inputfeed{version} =~ /(\\|\/)/) )
  	{
  		write_error_log("\nERROR: Invalid Artifact id or Version!\n");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  			$$inputfeed{group_id} =~ s#\\#\/#g;
  	1 while $$inputfeed{group_id} =~ s#^(\\|\/)##g;
  	1 while $$inputfeed{group_id} =~ s#(\\|\/)$##g;	
  	1 while $$inputfeed{group_id} =~ s#\\\\|\/\/#\/#g;
}

#################################################################################################################
# check genric arguments are passed correctly : Story-44832
#
sub genericArgumentCheck
{
	my $inputfeed 	= shift;
	my $line_number = shift;
  	if ((!$$inputfeed{repo}) || (!$$inputfeed{component}) || (!$$inputfeed{output_folder})) 
  	{
    	my $error_string  = "\nERROR: Arguments ";
    	   $error_string .= '-r <repo>, ' if (!$$inputfeed{repo});
    	   $error_string .= '-c <component>, ' if (!$$inputfeed{component});
    	   $error_string .= '-o <outputFolder>' if (!$$inputfeed{output_folder});
    	   $error_string  =~ s#, $##;
    	   
  		($line_number) ? ($error_string .= " missing at line $line_number !\n") : ($error_string .= " missing!\n");
  		write_error_log("$error_string");
    	displayUsage('generic_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}

  	if ($$inputfeed{group_id} || $$inputfeed{artifact_id} || $$inputfeed{version}) 
  	{
  		my $error_string  = "\nERROR: Extra arguments ";
  		   $error_string .= '-g <groupId>, ' if ($$inputfeed{group_id});
    	   $error_string .= '-a <artifactId>, ' if ($$inputfeed{artifact_id});
    	   $error_string .= '-v <version>' if ($$inputfeed{version});
  		   $error_string  =~ s#, $##;
  		   
  		($line_number) ? ($error_string .= " at line $line_number !\n") : ($error_string .= " !\n");
  		write_error_log("$error_string");
  		displayUsage('generic_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  			$$inputfeed{component} =~ s#\\#\/#g;
  	1 while $$inputfeed{component} =~ s#^(\\|\/)##g;
  	1 while $$inputfeed{component} =~ s#(\\|\/)$##g;
  	1 while $$inputfeed{component} =~ s#\\\\|\/\/#\/#g;
}

#################################################################################################################
# Remove space before and after the arguments : Story-44832
#
sub normaliseArguments
{
	my $arguments = shift;
	
	foreach my $key_argument (keys %{$arguments})
	{
		$$arguments{$key_argument} =~ s#^\s*##;
		$$arguments{$key_argument} =~ s#\s*$##;
	}
	return($arguments);
}
