#########################################################################################################################################################################
#																																										#
# FILE			:	deploy_folder_by_checksum.pl																														#
#																																										#																																										#
# DESCRIPTION	:	Recursively deploys folder content. Attempt checksum deploy first to optimize upload time.															#
#																																										#
# USAGE			:	perl deploy_folder_by_checksum.pl [ -h ] ( -m | -d ) -r <repo> -i <srcFolder> ( -c <component> |													#
#							( -g <groupId> -a <artifactId> -v <version>) [ -verbose ] [ -set ] [ -f ] [ -s <server> -u <userId> -p <password>                           #
#                             -useproxy ]                                                                                                                               #
#																																										#
# ARGUMENTS		:	see Usage																																			#
#																																										#
# COPYRIGHT		:	(c) 2014 Robert Bosch GmbH																															#
# HISTORY		:																																						#
#																																										#
# Date         	| Author                 		| Modification																											#
# 22.10.2014   	| M.Schoenfelder (ext)   		| Initial version																										#
# 22.06.2015   	| M.Schoenfelder (ext)   		| adapt to new config file																								#
# 09.09.2015   	| M.Schoenfelder (ext)   		| use Getopt::Long for better argument checking																			#
# 14.09.2015   	| M.Schoenfelder (ext)   		| do not allow spaces for -c, -g, -a and -v																				#
# 05.11.2015   	| Saddam hussain. A (RBEI/ECA2) | Adaption to maven and generic repository(can upload to maven and generic repository): Story-43037, 					#
#                                         		  Added log files for complete upload files, errro files, upload count, error count,time taken to upload : Story-43691,	#
#                                                 Appropriate Error message display handling : Story-43685,																#
#												  Force option to overwrite files : Story-43087,																		#
#                                                 Space handling in files and folder during upload(can upload files and folder with space) : Story-43685,				#
#                                                 Empty directory upload(Can upload empty folder)  : Story-43685,														#
#                                                 Extra input arguments handling(Exit if any anonymous input arguments passed) : Story-44832,							#
#                                                 User permission check before upload : Story-44168.																	#
# 10.12.2015   	| Saddam Hussain. A (RBEI/ECA2)	| Permission check before reading .artfiactory and reading source folder : Story-44832,									#
#												  JSON decoder used to parse json output from artifactory rest api : Story-44832.										#
# 03.03.2016	| Saddam hussain A 	(RBEI/ECA2)	| Adapt to new config file ( check settings, normalise path function) : story-52826										#
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled windows based execution : feature-76330                                                                       #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled verbose mode and progress bar: feature- 76327                                                                 #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled mac based execution : feature-76330                                                                           #
# 11.11.2016	| Sounak Patra (RBEI/ECA2)	    | Enabled option in upload script to set properties(RetC, PrjUsed) : feature-75045										#
# 07.04.2016	| Sounak Patra (RBEI/ECA2)      | Made modifications to handel HTTP 100 error codes																		#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | Made modifications to set property based on Artifactory version and added latest script version check functionality-	#
#												  story-165111																											#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		| Added feature to stop execution of older scripts: story-185699														#
# 31.05.2018	| Sounak Patra (RBEI/ECQ2)		| Fixed wrong md5 checksum generation in Mac OS: story-274782														    #
# 18.03.2019	| Sounak Patra (RBEI/ECQ2)		| Added noproxy option in curl                                                                                          #
# 18.10.2019	| Sounak Patra (RBEI/ECQ2)		| Made changes to upload pom file in bin mode                                                                           #
#																																										#
#########################################################################################################################################################################

use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use JSON qw( decode_json );
use Cwd;
use Cwd qw( abs_path );
use Getopt::Long;
use Data::Dumper;
#use warnings;

# Usage
my $usage = 
{
	'header'	=>	'Usage:',
	'prefix_arguments' => "perl $0",
	'all_arguments' => '[ -h ] ( -m | -d ) -r <repo> -i <srcFolder> ( -c <component> |( -g <groupId> -a <artifactId> -v <version>) [ -verbose ] [ -set ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'maven_arguments'=> ' -m -r <repo> -i <srcFolder> -g <groupId> -a <artifactId> -v <version> [ -verbose ] [ -set ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'generic_arguments' => ' -d -r <repo> -i <srcFolder> -c <component> [ -verbose ] [ -set ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'content' => 'Recursively deploys folder content. Attempt checksum deploy first to optimize upload time.',

	'description' =>
		{  
			'1'  => { '-h' =>  '-h                : Print this usage text.',},
    		'2'  => { '-m' =>  '-m <maven>        : For maven repository layout',},
    		'3'  => { '-d' =>  '-d <generic>      : For generic repository layout'},
    		'4'  => { '-r' =>  '-r <repo>         : Artifactory repository'},
    		'5'  => { '-i' =>  '-i <srcFolder>    : Source folder'},
    		'6'  => { '-c' =>  '-c <component>    : Component (target path inside repository)'},
    		'7'  => { '-g' =>  '-g <groupId>      : GroupId, use together with -a'},
    		'8'  => { '-a' =>  '-a <artifactId>   : ArtifactId, use together with -g'},
    		'9'  => { '-v' =>  '-v <version>      : Version of an artifact'},
    		'10' => {	'-verbose' =>  '-verbose	  : Verbose mode'},
    		'11' => { '-set'  	=>  '-set <property=value> : Property and value to be set'},
    		'12' => { '-f' =>  '-f <force>        : Force upload (optional, it will enable user to overwrite existing file inside repository. User should have DELETE permission)'},
    		'13' => { '-s' =>  '-s <server>       : Artifactory Server (optional, will override config file)'},
    		'14' => { '-u' =>  '-u <userId>       : Artifactory User ID (optional, will override config file)'},
    		'15' => { '-p' =>  '-p <password>     : Artifactory Password (optional, will override config file)'},
    		'17' => { '-useproxy' =>  '-useproxy         : Uses current proxy settings (optional, will override config file)'}
		},
    'end_content' => 'It is not allowed to deploy artifacts with spacing in names, so do not use spaces in options -c, -g -a and -v.',
                     "e.g.: -set argument pattern to pass inputs to the script
    				  perl $0 -set property1=value1,value2;property2=value3
    				  
    				  To set retention properties:
    				  perl $0 -set retc=2;prjused=GM,JACII "
};

# current date
my ($day, $mon, $year)  = (localtime)[3,4,5];
my $cur_date            = sprintf "%04d-%02d-%02d",($year+1900),($mon+1),$day;

# arguments
my ($server, $userId, $password, $verboseMode, $retCValue, $retPrjName, $external_properties, $repository_name, $no_proxy);
my $src_folder      = "";
my $component       = "";
my $version         = "";
my $repo            = "";
my $group_id        = "";
my $artifact_id     = "";

# derived from arguments
my $target_folder   = "";
my $pom_file	 	= "";

# other vars
my $auto_answer   			= $ENV{_SET_ENV_AUTO_ANSWER};
my $local_time				= localtime;
my $start_time				= time();
my $end_time				= 0;
my $uploaded_file_count		= "";
my $file_to_upload_count	= "";
my $overwritten_file_count  = "";
my $error_upload_file_count	= "";
my $error_string 			= "";
my $dev_nul 				= "/dev/null";
my $maven					= 0;       #maven repository upload
my $generic					= 0;	   #generice repository upload
my $force					= 0;	   #force upload
my $upload_log_file        	= 'upload.log';
my $error_log_file		   	= 'upload_error.log' ;

# Create log file
my $artifactoryLogDir = create_log_file( $upload_log_file,$error_log_file );
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

write_error_log("On Server\t: $server\n\n");
# Exit if server is not pingable or given repository not found
if( check_settings($server, $userId, $password, $repo, $no_proxy) ) 					# source repository existence check
{
	my 	$writeString			= "\nERROR: Target repository not found or user not having read permission to ";
		$writeString 	       .= "repository: $repo in artifactory server: $server\n\n";
   	write_error_log($writeString);
   	exit(1);
}

# check if source file exists and its a directory
if ((! -e $src_folder) && (! -d $src_folder)) 
{
   	write_error_log("ERROR: Source folder $src_folder does not exist or not a valid path.\n");
   	write_error_log("\n===========================================================================================================\n\n");
    exit(1);
}

# check for user permission in source folder
if (! -r $src_folder)
{
	write_error_log("User $userId is not having read permission to copy files from $src_folder\n");
  	write_error_log("\n===========================================================================================================\n\n");
  	exit(1);
}

createPom() if($maven);                #create pom file only if maven, for generic pom is not needed.
upload();
print "\n";
unlink($pom_file) if($maven);

if ($maven && $@)
{
	write_complete_log("$@\nWARNING: Error during deleting POM file - $pom_file\nDelete manualy the POM file if you are deploying from the same source folder\n");
}

# Calculate time to complete upload
$end_time 		= time();
my $duration 	= $end_time - $start_time;
my $minutes 	= int ( ( $duration / 60 ) % 60 );
my $seconds 	= $duration % 60;
my $hours 		= int( ( $duration /60) / 60 );
$error_upload_file_count = split('\n',$error_string);

# set default properties in case of no error
if ($error_string eq "") 
{
 	setProps();
	write_error_log("\nTotal no. of files: $file_to_upload_count, uploaded: $uploaded_file_count, failed: $error_upload_file_count, overwritten: $overwritten_file_count\n");
	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nUpload log         : $artifactoryLogDir$upload_log_file\n"; 
	print "Error log          : $artifactoryLogDir$error_log_file\n";
	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
}

# Check for intermediate errors and exit
if ($error_string ne "") 
{
	my $write_string = "\nFollowing problems occured during script execution:\n";
	   $write_string .= "----------------------------------------------------\n";
	   $write_string .= "$error_string\n\n";
	write_error_log($write_string);
	write_error_log("\nTotal no. of files: $file_to_upload_count, uploaded: $uploaded_file_count, failed: $error_upload_file_count, overwritten: $overwritten_file_count\n");
	write_error_log("Time taken: $hours hour $minutes minute $seconds second\n\n", $verboseMode);
	print "Refer log files for more details \nUpload log         : $artifactoryLogDir$upload_log_file\n"; 
	print "Error log          : $artifactoryLogDir$error_log_file\n";
	write_error_log("\n===========================================================================================================\n\n", $verboseMode);
	exit(1);
}
exit(0);
#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
#Display appropriate usage message based on the arguments(all_arguments, maven_arguments, generic_arguments) : Story-43685
#Example usage of maven deploy, here it showing only the arguments related to maven and not generic. 
#Usage:
#        perl deploy_folder_by_checksum.pl  -m -r <repo> -i <src_folder> -g <group_id> -a <artifact_id> -v <version> [-f] [-s <server>] [-u <usr_id> -p <pwd>]
#
#        Recursively deploys folder content. Attempt checksum deploy first to optimize upload time.
#
#        -m <maven>        : Maven repository upload
#        -r <repo>         : Artifactory Repository
#        -i <src_folder>   : Source folder
#        -g <group_id>     : GroupId, use together with -a
#        -a <art_id>       : ArtifactoryId, use together with -g
#        -v <version>      : Version of ArtifactoryId
#        -p <pwd>          : Artifactory Password (optional, will be read from config file)
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
		my @description_inner_key 		= keys %{$$usage{description}{$description_key}};
		if ($$usage{$argument_select}  	=~ /\s$description_inner_key[0]\s/)
		{
			$write_string  .= "\t$$usage{description}{$description_key}{$description_inner_key[0]}\n";
		}
	}
	$write_string .= "\n\t$$usage{end_content}\n\n";
	write_console($write_string);
}

#################################################################################################################
# create pom file to be able to retrieve version info in artifactory
#
sub createPom
{
	$pom_file = "$src_folder/$artifact_id-$version.pom";
  
	open (POM, ">$pom_file") or die "Could not create POM: $pom_file\n\n===========================================================================================================\n\n";
    binmode POM;
	print POM "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  	print POM "<project xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd\" xmlns=\"http://maven.apache.org/POM/4.0.0\"\n";
  	print POM "  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n";
  	print POM "  <modelVersion>4.0.0</modelVersion>\n";
  	print POM "  <groupId>$group_id</groupId>\n";
  	print POM "  <artifactId>$artifact_id</artifactId>\n";
  	print POM "  <version>$version</version>\n";
  	print POM "  <packaging>pom</packaging>\n";
  	print POM "  <description>generated POM</description>\n";
  	print POM "</project>\n";
  	close(POM);
}

#################################################################################################################
# get recursively files and folders list under windows : Story-44832
#
sub getFilesMswin
{
  	my @files_adapted 		= ();
  	my @empty_dir			= ();
  	my 	$src_folder_win     = $src_folder;
  		$src_folder_win		=~ s#\/#\\#g;
  	
  	my @dir_files 			= `dir /S /A:-D /B \"$src_folder_win\" 2>nul`;                  #list files except folders recursively under src_folder
  	my @all_dir 			= `dir /S /A:D /B \"$src_folder_win\" 2>nul`;					#list only folders recursivley under src_folder
  	foreach my $dir (@all_dir)
  	{
  		chomp($dir);
  		my @all_dir_rec 	= `dir /S /A:-D /B \"$dir\" 2>nul`;
    	push(@empty_dir,$dir) if ($#all_dir_rec < 0);                          			#empty directories under src_folder fetched recursively by checking any files under it 
  	}
  	#print Dumper (\@all_dir,\@files_adapted,\@empty_dir);
  	return(\@dir_files,\@empty_dir);
  	  	
}

#################################################################################################################
# get recursively files and folders list under linux 
#
sub getFilesLinux
{
  	my @files_adapted 		= ();
  	my @empty_dir			= ();
  	
  	my @dir_files 			= `find \"$src_folder\" -type f`;                   		#list files except folders recursively under src_folder
  	my @all_dir 			= `find \"$src_folder\" -type d`;					  		#list only folders recursivley under src_folder
  	foreach my $dir (@all_dir)
  	{
  		chomp($dir);
  		my @all_dir_rec 	= `find \"$dir\" -type f`;
    	push(@empty_dir,$dir) if ($#all_dir_rec < 0);                          			#empty directories under src_folder fetched recursively by checking any files under it 
  	}
  	#print Dumper (\@all_dir,\@files_adapted,\@empty_dir);
  	return(\@dir_files,\@empty_dir);
  	  	
}

#################################################################################################################
# upload files : Story-43685(Empty directory upload)
#
sub upload
{
	my @files					= ();
	my @empty_dir				= ();
	my $temp_file				= "";
	my $temp_dir				= "";
	   $overwritten_file_count 	= 0;
	   $uploaded_file_count		= 0;
	my $file_upload_progress	= 0;
	my $src_folder_win			= "";
	my ($temp1,$temp2)		    = 0;

	if ($^O =~ /mswin/i)
	{
    	($temp1,$temp2) = getFilesMswin();
    	@files  		= @$temp1;
    	@empty_dir 		= @$temp2;
    	$src_folder_win	= $src_folder;
		$src_folder_win	=~ s#\/#\\#g; 
	}
	elsif ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i)
	{
		($temp1,$temp2) = getFilesLinux();
    	@files  		= @$temp1;
    	@empty_dir 		= @$temp2;
	}
 
	$local_time = localtime;
    my 	$write_string   = "Uploading from $src_folder to $repo/$target_folder/...\n";
  	   	$write_string  .= "Operation(mode)    : upload(force)\n" if ($force);
  	   	$write_string  .= "Operation(mode)    : upload(non-force)\n\n" unless ($force);
  	   
	write_error_log($write_string, $verboseMode);
  	$file_to_upload_count = scalar @files;

	my ($md5_value, $sha1_value);
	my $upload_progress	= 0;
  	my $def_percentage_counter = 0;
  	   $def_percentage_counter = (100 / $file_to_upload_count) if ($file_to_upload_count);
	
  	foreach my $file (@files) 
  	{
    	chomp($file);
    	if (not $verboseMode)
    	{
    		$upload_progress ++;
    		get_progress_percentage(int($def_percentage_counter * $upload_progress), "Upload");
    	}

    	if ($file 	=~ /_content.sha1/i or ($file =~ /\.pom$/i and basename($file) ne basename($pom_file)))
    	{
    		$file_to_upload_count--;
    		next;
    	}
    	
    	$file_upload_progress++;
    	$file 			=~ s#^\\\\#\\\\\\\\# if ($^O =~ /mswin/i);             	# incase of UNC path replace \\ with \\\\                          

    	# generate checksums    	
    	$md5_value  = get_hash_value('MD5', $file);
    	$sha1_value = get_hash_value('SHA1', $file);

		# for UNC path escape all the slashes
		$file 			=~ s#^\\\\\\\\#\\\\# if ($^O =~ /mswin/i);   	
    	my $rel_file 	=  $file; 								           	 	# filename relative to src_folder
    	$rel_file 		=~ s#.*\Q$src_folder_win\E\\##;                         	# replace src_folder in files full path to get files to upload incase windows   
    	$rel_file 		=~ s#.*\Q$src_folder\E\/##;                         		# replace src_folder in files full path to get files to upload incase linux
    	$rel_file 		=~ s#\\#/#g;
    	$temp_file		=  $rel_file;
    	$rel_file       =~ tr/%/ /;
    	$rel_file 		=~ s#\s+#%20#g;                                      	#replace if files or directory have space with %20

    	my $depoly_progress	= "($file_upload_progress\/$file_to_upload_count)";
        write_complete_log("$depoly_progress .../$temp_file - ", $verboseMode);

    	# Search for file exist
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
        $cmd .= "-s -X GET \"$server/api/storage/$repo/$target_folder/$rel_file\" --output $dev_nul --write-out \"%{http_code}\"";
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
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
        $cmd .= "-s -X PUT -H \"X-Checksum-Deploy:true\" -H \"X-Checksum-Sha1:$sha1_value\" -H \"X-Checksum-Md5:$md5_value\" ";
       	$cmd .= "--write-out \"%{http_code}\" --output $dev_nul \"$server/$repo/$target_folder/$rel_file\"";
    	my $status2 = `$cmd`;
    	
    	if ($status2 eq "404") 
    	{ # checksum not found -> deploy/upload file
      		if ($status1 eq "404" || $force) 
      		{
        		# Upload
                my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
        		$cmd .= "-s -H \"X-Checksum-Sha1:$sha1_value\" -H \"X-Checksum-Md5:$md5_value\" ";
        		$cmd .= "--write-out \"%{http_code}\" --output $dev_nul -T \"$file\" \"$server/$repo/$target_folder/$rel_file\"";
        		my $status_upload = `$cmd`;  # upload if file not exist or force enabled

        		if ($status_upload =~ /^2/ || $status_upload =~ /^1/) 
        		{ # upload ok , print status
        			if ($status1 ne "404")
      				{
						write_complete_log("Upload ok(File exist and overwritten): $status_upload\n", $verboseMode);
						$overwritten_file_count++;
					}
      				else
      				{
						write_complete_log("Upload ok: $status_upload\n", $verboseMode);
					}
					$uploaded_file_count++;
        		}
      			else
      			{ # error from upload
					write_complete_log("\n ERROR during upload: $status_upload\n", $verboseMode);
        			$error_string .= "Error upload: $status_upload - $file\n";
      			}
    		}
    		elsif (($status1 =~ /^4/) || ($status1 =~ /^5/)) 
    		{
                # other error from file search, client error 4xx or server error 5xx
				write_complete_log("\n ERROR during search for file: $status1\n", $verboseMode);
      			$error_string .= "Error file search: $status1 - $file\n";
    		}
    		else  
    		{
				write_error_log("\n ERROR during upload: File exist with same name. If you want to overwrite file, select force option (-f) and user should have DELETE permission on $repo\n", $verboseMode);
    			unlink($pom_file) if($maven);
				if ($maven && $!)
				{
					write_complete_log("$!\nWARNING: Error during deleting POM file - $pom_file\nDelete manualy the POM file if you are deploying from the same source folder\n", $verboseMode);
				}
    			write_error_log("\n===========================================================================================================\n\n", $verboseMode);
    			exit(1);
    		}
    	}
    	elsif (($status2 =~ /^4/) || ($status2 =~ /^5/)) 
    	{
            # other error from checksum, client error 4xx or server error 5xx
			write_complete_log("\n ERROR during search for checksum: $status2\n", $verboseMode);
      		$error_string .= "Error checksum: $status2 - $file\n";
    	}
    	else 
    	{
            # should be ok, print status for info
    		if ($status1 eq "404")
    		{
    			write_complete_log("Upload ok : $status2\n", $verboseMode);             
				$uploaded_file_count++;  # only counted if file is not there in current version eventhough checksum is availabe somewhere else
    		}
    		else
    		{
    			write_complete_log("Checksum ok: $status2\n", $verboseMode);  # checksum matched under current folder, files will not be uploaded only mapped
    		}  
    	}
	}
	
	# upload empty directories (uploaded empty directory will not be counted in uploaded count)
	foreach my $dir (@empty_dir)                      
  	{
    	chomp($dir);
    	my $rel_dir 	= $dir;  # filename relative to src_folder
    	$rel_dir 		=~ s#.*\Q$src_folder_win\E\\##;
    	$rel_dir 		=~ s#.*\Q$src_folder\E\/##;
    	$rel_dir 		=~ s#\\#/#g;
    	$temp_dir		=  $rel_dir;
    	$rel_dir 		=~ s#\s+#%20#g;  #replace if files or directory have space with %20
      	
        write_complete_log(".../$temp_dir - ", $verboseMode);
		
    	#Search for directory exist
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    	$cmd .="-s -X GET \"$server/api/storage/$repo/$target_folder/$rel_dir/\" --output $dev_nul --write-out \"%{http_code}\"";
    	my $status = `$cmd`;

    	if ($status eq "404") 
    	{
            $cmd = set_curl_command($no_proxy, $userId, $password, 0);
        	$cmd .= "-X PUT \"$server/$repo/$target_folder/$rel_dir/\" --write-out \"%{http_code}\" --silent --output $dev_nul";
        	my $status_upload 	= `$cmd`;
        	if ($status_upload 	=~ /^2/) 
        	{ # upload ok , print status
				write_complete_log("Upload ok: $status_upload\n", $verboseMode);
				#$uploaded_file_count++;
        	}
      		else
      		{ # error from upload
				write_complete_log("\n ERROR during upload: $status_upload\n", $verboseMode);
        		$error_string  .= "Error upload: $status_upload - $dir\n";
      		}
    	}
    	elsif (($status =~ /^4/) || ($status =~ /^5/)) 
    	{ # other error from checksum, client error 4xx or server error 5xx
			write_complete_log("\n ERROR during search for Directory: $status\n", $verboseMode);
      		$error_string  .= "Error search directory: $status - $dir\n";
    	}
    	else 
    	{ # should be ok, print status for info
			write_complete_log("Directory exist ok: $status\n", $verboseMode);
			#$uploaded_file_count++;
    	}
	}
}

#################################################################################################################
# set default properties on version directory
#
sub setProps
{
  	my 	$script_dir = dirname($0);
	my $artifactory_version = get_artifactory_version($server, $no_proxy);
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
  	$cmd .= "-sS -X PUT $server/api/storage/$repo/$target_folder?properties=";

	if ($artifactory_version >= 5.0) 
	{
	    if ($external_properties eq "")
	    {
	    	write_complete_log("\nProperties retention.RetDate=$cur_date;retention.PrjUsed=$retPrjName;retention.RetC=$retCValue&recursive=0 set -");
	    	$cmd .= "\"retention.RetDate=$cur_date;retention.PrjUsed=$retPrjName;retention.RetC=$retCValue&recursive=0\"";
	    }
	    else
	    {
	    	write_complete_log("\nProperties retention.RetDate=$cur_date;retention.PrjUsed=$retPrjName;retention.RetC=$retCValue". ";" . $external_properties . "&recursive=0 set -");
	    	$cmd .= "\"retention.RetDate=$cur_date;retention.PrjUsed=$retPrjName;retention.RetC=$retCValue". ";" . $external_properties . "&recursive=0\"";
	    }		
	}
	else
	{
	    if ($external_properties eq "")
	    {
	    	write_complete_log("\nProperties retention.RetDate=$cur_date|retention.PrjUsed=$retPrjName|retention.RetC=$retCValue&recursive=0 set -");
	    	$cmd .= "\"retention.RetDate=$cur_date|retention.PrjUsed=$retPrjName|retention.RetC=$retCValue&recursive=0\"";
	    }
	    else
	    {
	    	write_complete_log("\nProperties retention.RetDate=$cur_date|retention.PrjUsed=$retPrjName|retention.RetC=$retCValue". "|" . $external_properties . "&recursive=0 set -");
	    	$cmd .= "\"retention.RetDate=$cur_date|retention.PrjUsed=$retPrjName|retention.RetC=$retCValue". "|" . $external_properties . "&recursive=0\"";
	    }		
	}
    
  	my $output = `$cmd`;
  	if ($output)
  	{
  		my $decodeJson = decode_json($output) ;
  		if (defined $decodeJson->{'errors'} )
  		{
  			write_error_log("$$decodeJson{errors}[0]{status} - ERROR: Failed setting artifact: $target_folder properties - Message: $$decodeJson{errors}[0]{message}\n\n");
  		}
  	}
  	else 
  	{
    	write_complete_log(" Ok\n");
  	}
}

#################################################################################################################
# remove square brackets and check any special characters are present or not: feature-75045
#
sub modifyPropertyValue
{
	my ($value) = @_;
	if ($value =~ /^\[/)
  	{
  		$value =~ tr/[/ /;
		$value =~ tr/]/ /;
		$value =~ s/^\s+|\s+$//g;
  	}

  	return $value;
}

#################################################################################################################
# get values from user defined properties: feature-75045
#
sub getPropertyValues
{
	my ($propValue) = @_;
	($retCValue, $retPrjName, $external_properties) = (3, "", "");
	my %properties;
	
  	if ($propValue)
  	{
	  	my @values = split(';', $propValue);
	  	foreach my $i (@values)
	  	{
	  		my @prop = split('=', $i);
	  		if (scalar @prop > 1)
	  		{
	  			my $property = $prop[0];
	  			
		  		if ((lc($property) eq "retc") || (lc($property) eq "retention.retc"))
		  		{
		  			$retCValue = $prop[1];
		  		}
		  		elsif ((lc($property) eq "prjused") || (lc($property) eq "retention.prjused"))
		  		{
		  			$retPrjName = $prop[1];
		  		}
		  		elsif ((lc($property) ne "retdate") || (lc($property) ne "retention.retdate"))
		  		{
		  			$properties{$prop[0]} = $prop[1];
		  		}	  			
	  		}
	  		else
	  		{
				write_error_log("\nERROR: Please provide value for the property: $prop[0]\n");
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
	  		}	  		  		
	  	}
	  	
		foreach my $key (keys %properties)
		{	
			my $prop_val =  (modifyPropertyValue($key) . "=" .
						     modifyPropertyValue($properties{$key}));					
			$external_properties = ((($external_properties eq "") ? "" :
									  $external_properties . "|") . $prop_val);
		} 
  	}
  	
  	$retCValue = modifyPropertyValue($retCValue);
  	$retPrjName = modifyPropertyValue($retPrjName);
	
  	if ($retCValue !~ /^[2-4]$/) 
  	{
  		write_error_log("\nERROR: RetC value should be 2,3 or 4\n");
		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}  	
}


#################################################################################################################
# scan arguments and assign them to global script variables : Story-43685 (Appropriate error message display for maven and generic), Story-44832(if any anonymous input arguments passed)
# show help text if arguments are not set correctly
#
sub scanArgs
{
  	my ( $h, $verbose, $setProps, $useproxy );
  	my $res = GetOptions (
   	'h'      => \$h,
   	'm'		 => \$maven,
   	'd'		 => \$generic,
   	'f'		 => \$force,
   	'u=s'    => \$userId,
   	'p=s'    => \$password,
   	'i=s'    => \$src_folder,
   	's=s'    => \$server,
   	'r=s'    => \$repo,
   	'c=s'    => \$component,
   	'g=s'    => \$group_id,
   	'a=s'    => \$artifact_id,
   	'v=s'    => \$version,
    'useproxy'    => \$useproxy,
   	'verbose'    => \$verbose,
   	'set=s'		 	=> \$setProps,
  	) or do {
  				write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  				displayUsage('all_arguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
  			}; 

	$repository_name = $repo;
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
  	unless ( $maven || $generic)
  	{
  		write_error_log("\nERROR: Arguments missing!\nRepository type should be given in the arguments as (either -m for maven or -d for generic)\n");
		displayUsage('all_arguments');
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
  	}
  	if ($maven && $generic)
  	{
  		write_error_log("\nERROR: Extra argument, either generic or maven option can be selected\n");
  		displayUsage('all_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	
  	if (not $verbose){$verboseMode = 0} else {$verboseMode = 1};
  	
  	getPropertyValues($setProps);
 	
	# Corresponding arguments check
	($maven)? mavenArgumentCheck() : genericArgumentCheck();
	
  	# normalise path
  	$src_folder = normalise_path($src_folder);
  	if ( $src_folder == 1 )
	{
		write_error_log("\nERROR: Invalid Output file: $src_folder path!\n");
		( $maven ) ? ( displayUsage('maven_arguments') ) : ( displayUsage('generic_arguments') );
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
	}

  	$component        	=~ s#\\#\/#g;  #correct if slashes are mistakenly given wrong
  	$group_id      	  	=~ s#\\#\/#g;

  	write_complete_log("\nWARNING: Force option selected and file will be overwritten if already exist!\n") if ($force);
  
  	if ($maven){
  		$target_folder    	= $group_id."/".$artifact_id."/".$version
  	}
  	elsif ($generic){
  		$target_folder	  	= $component
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
# check maven arguments are passed correctly : Story-44832
sub mavenArgumentCheck
{	
	if ((!$repo) || (!$group_id) || (!$artifact_id) || (!$version) || (!$src_folder)) 
  	{
  		my $error_string  = "\nERROR: Arguments ";
  		   $error_string .= '-r <repo>, ' if (!$repo);
  		   $error_string .= '-g <groupId>, ' if (!$group_id);
    	   $error_string .= '-a <artifactId>, ' if (!$artifact_id);
    	   $error_string .= '-v <version>, ' if (!$version);
    	   $error_string .= '-i <srcFolder>' if (!$src_folder);
    	   $error_string  =~ s#, $##;
    	   $error_string .= " missing!\n";
  		write_error_log("$error_string");
    	displayUsage('maven_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	# extra arguments check	
  	if ($component) 
  	{
  		write_error_log("\nERROR: Extra -c <component> argument!\n");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	# artifact id and version correctness check 
  	if ( ($artifact_id =~ /(\\|\/)/) || ($version =~ /(\\|\/)/) )
  	{
  		write_error_log("\nERROR: Invalid Artifact id or Version!\n");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	if ($group_id =~ /\s/ || $artifact_id =~ /\s/ ) 
  	{
  		write_error_log("\nERROR: Group_Id and/or Artifact_ID contains a space, it is not allowed to deploy folders containing spaces!\n");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	if ($version =~ /\s/) 
  	{
  		write_error_log("\nERROR: Version contains a space, it is not possible to deploy folders containing spaces!\n");
		displayUsage('maven_arguments');
		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  			$group_id =~ s#\\#\/#g;
  	1 while $group_id =~ s#^(\\|\/)##g;
  	1 while $group_id =~ s#(\\|\/)$##g;
  	1 while $group_id =~ s#\\\\|\/\/#\/#g;
}

#################################################################################################################
# check genric arguments are passed correctly : Story-44832
#
sub genericArgumentCheck
{
  	if ((!$repo) || (!$component) || (!$src_folder)) 
  	{
  		my $error_string  = "\nERROR: Arguments ";
    	   $error_string .= '-r <repo>, ' if (!$repo);
    	   $error_string .= '-c <component>, ' if (!$component);
    	   $error_string .= '-i <srcFolder>' if (!$src_folder);
    	   $error_string  =~ s#, $##;
    	   $error_string .= " missing!\n";
    	   
    	write_error_log("$error_string");
    	displayUsage('generic_arguments');
    	write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  	if ($group_id || $artifact_id || $version) 
  	{
  		my $error_string  = "\nERROR: Extra arguments ";
  		   $error_string .= '-g <groupId>, ' if ($group_id);
    	   $error_string .= '-a <artifactId>, ' if ($artifact_id);
    	   $error_string .= '-v <version>' if ($version);
  		   $error_string  =~ s#, $##;
  		   $error_string .= " !\n";
  		   
  		write_error_log("$error_string");
  		displayUsage('generic_arguments');
		write_error_log("\n===========================================================================================================\n\n");
  		exit(1);
  	}
  	if ($component =~ /\s/) 
  	{
  		write_error_log("\nERROR: Component contains a space, it is not possible to deploy folders containing spaces!\n");
  		displayUsage('generic_arguments');
  		write_error_log("\n===========================================================================================================\n\n");
    	exit(1);
  	}
  			$component =~ s#\\#\/#g;
  	1 while $component =~ s#^(\\|\/)##g;
  	1 while $component =~ s#(\\|\/)$##g;
  	1 while $component =~ s#\\\\|\/\/#\/#g;
}
