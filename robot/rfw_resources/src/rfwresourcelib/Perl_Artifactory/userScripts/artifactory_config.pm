#################################################################################################################################
#                                                                                                                               #
# FILE			:	artifactory_config.pm																						#
#                                                                                                                               #
# DESCRIPTION	:	perl package for artifactory configuration																	#
#                                                                                                                               #
# COPYRIGHT		:	(c) 2014 Robert Bosch GmbH																					#
# HISTORY		:																												#
# Date         	| Author                		| 	Modification																#
# 17.10.2014   	| M.Schoenfelder (ext)  		| 	Initial version																#
# 19.06.2015   	| M.Schoenfelder (ext)  		| 	read settings from config file in homedir									#
# 05.11.2015   	| Saddam hussain. A (RBEI/ECA2) | 	create log file under Artifactory in user temp folder,						#
#										  			write log into stdout, complete and error log based on user selection,		#
#                                         			check user permission for the given repository. 							#
# 01.03.2016	| Saddam hussain A (RBEI/ECA2)	| 	check settings, normalise path, ping server, get encrypt password functions #
#										  			added : story-52831														    #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled windows based execution                                             #
#													feature- 76330                                                              #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled verbose mode and progress bar                                       #
#													feature- 76327                                                              #
# 28.09.2016	| Sounak Patra (RBEI/ECA2)	    | 	Enabled mac based execution                                                 #
#													feature- 76330                                                              #
# 01.12.2016	| Sounak Patra (RBEI/ECA2)	    |	Updated error message on password change									#
# 09.02.2017	| Sounak Patra (RBEI/ECA2)	    |	Modified code to handle special characters in password						#
# 07.04.2017	| Sounak Patra (RBEI/ECA2)      | 	Modified code to handle connection timeout									#
# 26.06.2017	| Sounak Patra (RBEI/ECA2)      | 	Removed dependency on windows certutil and added method to get artifactory	#
#													instance version: story-165111												#
# 05.09.2017	| Sounak Patra (RBEI/ECA2)		|   Added feature to generate file to store md5 values: story-178336			#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		|	Added feature to stop execution of older scripts: story-185699				#
# 20.12.2017	| Sounak Patra (RBEI/ECA2)		| 	Updated information message to create config file: story-222017			    #
# 12.04.2018	| Sounak Patra (RBEI/ECA2)		| 	Added feature to update ssl certificates to use https connection:		    #
#													story-246847																#
# 31.05.2018	| Sounak Patra (RBEI/ECQ2)		| 	Updated script version for md5 checksum fix in Mac OS:story-274782 			#
# 10.09.2018	| Sounak Patra (RBEI/ECQ2)		| 	Added feature to update certificate for https in Mac OS			 			#
# 17.09.2018	| Sounak Patra (RBEI/ECQ2)		| 	Removed dependency on digest package for checksum generation in Linux       #
# 15.02.2019	| Sounak Patra (RBEI/ECQ2)		| 	Added noproxy option in curl                                                #
#                                                                                                                               #
#################################################################################################################################
#!/usr/bin/perl
#package artifactory_config;

use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Path;
use File::Basename;
use File::Copy;
use File::Spec::Functions 'catfile';
use strict;
use Exporter;
use JSON qw( decode_json);
use Cwd;
use Data::Dumper;
if ($^O =~ /mswin/i || $^O =~ /darwin/i)
{
	use Digest::file qw(digest_file_hex);
}
use MIME::Lite;


our @ISA 	= ('Exporter');
our @EXPORT = ('read_from_config','check_env','read_server_info','create_log_file','write_console','write_complete_log',
               'write_error_log','permission','normalise_path','check_settings','get_password');

# current script version
our $scriptVersion = 4.2;
my ( $artifactoryLogDir, $cfg );

if ($^O =~ /mswin/i || $^O =~ /cygwin/i)
{
	$artifactoryLogDir      		= "$ENV{USERPROFILE}\\Artifactory_log\\" ;		# artifactory log directory
	$cfg							= "$ENV{USERPROFILE}\\\.artifactory" ;			# artifactory config file ( server, userId and password is stored here )
}
elsif ($^O =~ /linux/i)
{
	if (defined($ENV{HOME}))
	{
		$artifactoryLogDir      = $ENV{HOME}."/Artifactory_log/";
		$cfg                    = $ENV{HOME}."/\.artifactory" ;
	}
	else
	{
		$artifactoryLogDir      = "/home/$ENV{USER}/Artifactory_log/";
		$cfg                    = "/home/$ENV{USER}/\.artifactory" ;
	}
}
elsif ($^O =~ /darwin/i)
{
   $artifactoryLogDir      		= "/Users/$ENV{USER}/Artifactory_log/";
   $cfg							= "/Users/$ENV{USER}/\.artifactory" ;	
}

##############################################################################################################
# exported functions
##############################################################################################################
# creates noproxy using server domain
#
sub create_no_proxy
{
    my ($server) = @_;
    my @data = split /\//, $server;
	
    return $data[2];
}

# set basic curl command based on proxy settings
#
sub set_curl_command
{
    my ($noproxy, $userId, $password, $need_timeout) = @_;
    my $cmd;

	if ($userId ne "" && $need_timeout)
    {   
        if ($^O =~ /mswin/i || $^O =~ /cygwin/i)
        {
            $cmd =  "curl --connect-timeout 10 --noproxy \"$noproxy\" -u \"$userId:$password\" ";
        }
        elsif ($^O =~ /linux/i || $^O =~ /darwin/i)
        {
            $cmd =  "curl --connect-timeout 10 --noproxy \"$noproxy\" -u '$userId:$password' ";
        }
    }
	if ($userId ne "" && !$need_timeout)
    {   
        if ($^O =~ /mswin/i || $^O =~ /cygwin/i)
        {
            $cmd =  "curl --noproxy \"$noproxy\" -u \"$userId:$password\" ";
        }
        elsif ($^O =~ /linux/i || $^O =~ /darwin/i)
        {
            $cmd =  "curl --noproxy \"$noproxy\" -u '$userId:$password' ";
        }
    }
	elsif ($userId eq "" && !$need_timeout)
    {   
        $cmd = "curl --noproxy \"$noproxy\" ";
    }
	elsif ($userId eq "" && $need_timeout)
    {   
        $cmd = "curl --connect-timeout 10 --noproxy \"$noproxy\" ";
    }

    return $cmd;
}

# ping server : story-52831
#
sub ping_server
{
	my ($serverReceived, $noproxyReceived, $userIdReceived, $passwordReceived) = @_;
	my $pingCmd;
	if ( scalar @_ == 4 )
	{
        $pingCmd = set_curl_command($noproxyReceived, $userIdReceived, $passwordReceived, 1);
        $pingCmd .= "-X GET -s -S \"$serverReceived/api/system/ping\"";
	}
	else
	{
        $pingCmd = set_curl_command($noproxyReceived, "", "", 1);
        $pingCmd .= "-X GET -s -S \"$serverReceived/api/system/ping\"";
	}
	my $pingStatus 	= `$pingCmd`;
	if ( $pingStatus =~ /^ok$/i )
	{
		return (0);
	}
	else
	{	
		if (scalar @_ == 4)
		{
            write_error_log("\nERROR: Server: $serverReceived is not accessible for given userId and Password. Password might have expired or check Artifactory server URL!!\n");
		}
        else
		{
            write_error_log("\nERROR: Server: $serverReceived is not accessible\n");
        }
        write_error_log("\n$pingStatus\n");
		return (1);
	}
}

##############################################################################################################
# read server info, user and pwd from config file
#
sub read_from_config 
{
	my ($cfgServer, $cfgUserId, $cfgPassword, $cfgProxy);

    if (! -e $cfg)
    {
        write_error_log("#########################################################################################\n\n");
        write_error_log("Please create configfile $cfg by using command:\nperl $Bin/create_artifactory_cfg.pl\n\n");
        write_error_log("#########################################################################################\n");
        exit(1);
    }
    else
    {
        open(CONFIG, "<$cfg") or die "$cfg cannot be opened!\n\n===========================================================================================================\n\n";
        my @lines = <CONFIG>;
        close(CONFIG);
        foreach my $line (@lines) 
        {
            $line =~ s/\s*//g; # remove spaces
            next if ($line =~ /#/ ); # ignore comments
            if ($line =~ /server=/i)  {(undef,$cfgServer)    = split(/=/,$line);}
            if ($line =~ /user=/i)    {(undef,$cfgUserId)    = split(/=/,$line);}
            if ($line =~ /pwd=/i)     {(undef,$cfgPassword)  = split(/=/,$line);}
            if ($line =~ /noproxy=/i)     {(undef,$cfgProxy)  = split(/=/,$line);}
  		}
        $cfgServer 		=~ s#[\\\/]+$##;

		if ($cfgProxy eq "")
		{
            write_complete_log("WARNING: Kindly update $cfg file to update proxy configuration\n")
		}

  		# check settings
  		if ( ($cfgServer eq "") || ($cfgUserId eq "") || ($cfgPassword eq "") ) 
  		{
            my $errorString = '';
  			$errorString  = "ERROR: Problem in reading artifactory config file $cfg\n";
    		$errorString .= "You will not be able to deploy to or download from Artifactory.\n";
    		write_error_log( $errorString );
    		exit(1);
  		}
        else
        {
            my $ping_status = ping_server($cfgServer, $cfgProxy, $cfgUserId, $cfgPassword);
            if ($ping_status)
            {
               write_error_log("#########################################################################################\n\n");
               write_complete_log( "INFO: Please update your password by using command:\t\t\t\t\n\tperl $Bin/create_artifactory_cfg.pl update\n\n" );
               write_error_log("#########################################################################################\n\n");
               exit(1);
            }
			return ($cfgServer, $cfgUserId, $cfgPassword, $cfgProxy);
        }
	}
}

##############################################################################################################
# returns error message based on error code
#
sub check_error_code
{
    my ($data) = @_;
    my $err_msg = "";
	my %err_code_data = ("400" => "Bad Request",
                         "401" => "Wrong Credentials",
                         "403" => "Forbidden",
                         "404" => "File Not Found",
                         "405" => "Method Not Allowed",
                         "406" => "Not Acceptable",
                         "408" => "Request Timeout",
                         "500" => "Internal Server Error",
                         "501" => "Not Implemented",
                         "502" => "Bad Gateway",
                         "503" => "Service Unavailable");

	foreach my $key (keys %err_code_data)
    {
        if (index($data, $key) != -1)
        {
            $err_msg = $err_code_data{$key};
        }
    }

	return ($err_msg);
}

##############################################################################################################
# returns error message based on error code from curl output
#
sub parse_curl_error_output
{
    my ($data) = @_;
    my $err_msg = "";

    $err_msg = check_error_code($data);

    return $err_msg;
}

##############################################################################################################
# get encrpted by passing new password : story-52831
#
sub get_encrypted_password
{
	my ( $serverReceived, $userIdReceived, $passwordReceived, $noproxyReceived ) = @_;
	
    my ($encCmd, $newEncryptPassword);
    $encCmd = set_curl_command($noproxyReceived, $userIdReceived, $passwordReceived, 1);
    $encCmd .= "-X GET -s -S \"$serverReceived/api/security/encryptedPassword\"";
    $newEncryptPassword = `$encCmd`;

    if ($newEncryptPassword =~ /errors/ || $newEncryptPassword =~ /^$/ ) 
    {    
        my @resultvalues = split(/\n/, $newEncryptPassword);
        my $err_code =  parse_curl_error_output($newEncryptPassword);
        if ($err_code ne "")
        {
            write_error_log("ERROR MESSAGE: $err_code");
        }
    	write_error_log("\nERROR: Problem in interacting with artifactory server: $serverReceived, Could not get encrypted password, abort...\n");
    	return (1);
    }
	else
    {
        return ($newEncryptPassword);
	}
}

##############################################################################################################
# write server details and user credentials to config file
#
sub write_to_config
{
    my ($serverReceived, $userIdReceived, $passwordReceived, $noproxyReceived, $cfgReceived) = @_;
    $cfgReceived 	=~ s#\\#\/#g;     # normalise slash
    open(CONFIG, ">$cfgReceived") or die "$cfgReceived cannot be opened!\n\n===========================================================================================================\n\n";
    print CONFIG "SERVER=$serverReceived\n";
    print CONFIG "USER=$userIdReceived\n";
    print CONFIG "PWD=$passwordReceived\n";
    print CONFIG "NOPROXY=$noproxyReceived";
    close(CONFIG);

    if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O !~ /darwin/i)
    {
        chmod 0600 , $cfgReceived or write_complete_log("\nWARNING: Could not change file permissions, please execute chmod 600 $cfgReceived\n"); 			
    }
    return (0);
}

##############################################################################################################
# read server info only from config file
#
sub read_server_info 
{
  	# read standard config file
  	open(CONFIG, "<$cfg") or die "$cfg cannot be opened!\n\n===========================================================================================================\n\n";
  	my @lines = <CONFIG>;
  	close(CONFIG);
  	my $server;
  	foreach my $line (@lines) 
  	{
    	$line =~ s/\s*//g;          # remove spaces
    	next if ($line =~ /#/ );    # ignore comments
    	if ($line =~ /server=/i)  {(undef,$server)    = split(/=/,$line);}
  	}	
  	return($server);
}

##############################################################################################################
# artifactory scripts must be executed in cygwin shell or linux (md5sum, sha1sum etc. required)
# check functionality of md5sum
#
sub check_env 
{
  	if ($^O !~ /cygwin/i && $^O !~ /mswin/i && $^O !~ /linux/i && $^O !~ /darwin/i) 
  	{
    	write_error_log("ERROR: Environment not supported! Use cygwin or execute under linux\n");
    	return(1);
  	}
  	my $dev_nul = "";
    my $cmd = "";
 
    if ($^O =~ /linux/i || $^O =~ /cygwin/i)
    {
    	$dev_nul = "/dev/null";
  		$cmd   = "md5sum $0 > $dev_nul"; 		   	
    }
	elsif ($^O =~ /mswin/i)
	{
		$dev_nul = "NUL";
  		$cmd = "certUtil -hashfile $0 MD5 > $dev_nul"; 
	}
	elsif ($^O =~ /darwin/i)
	{
		$dev_nul = "/dev/null";
		$cmd = "md5 $0 > $dev_nul";
	}

	my $res   = system($cmd);

  	if ($res and ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i))
  	{ 
  		write_error_log("\nERROR: Environment not setup correctly, you will need md5sum, sha1sum,... \n use cygwin or execute under linux or mac\n");
  		return(1);
  	}
  	elsif ($res and $^O =~ /mswin/i)
  	{
  		write_error_log("\nERROR: Environment not setup correctly");
  		return(1);  		
  	}
  	else      { return(0);}   # env ok
}

##############################################################################################################
# create log file under Artifactory in user temp folder
#
sub create_log_file
{
	my ( $complete_log, $error_log) 	= @_ ;
	$complete_log 						= $artifactoryLogDir.$complete_log;
	$error_log 							= $artifactoryLogDir.$error_log;
	if(! -d $artifactoryLogDir)
	{
		print "Artifactory_log directory not exist, creating path $artifactoryLogDir...\n";
		if(-w dirname($artifactoryLogDir))
		{
			eval { mkpath($artifactoryLogDir) };
			if ($@)
			{
				print "Artifactory_log directory not exist, creating path $artifactoryLogDir...\n";
				print "Not able to create path $artifactoryLogDir, check the error.\n\n";
				return(1);
			}
		}
		else
		{
			print "User is not having permission to create folder: $artifactoryLogDir or not a valid path\n";
			print "\n===========================================================================================================\n\n";
			return(1);
		}
	}  
	 
	# Log File creation
	open (COMPLETE_LOG,'>>',$complete_log) or die "Not able to open complete log file: $complete_log\n\n===========================================================================================================\n\n";
	open (ERROR_LOG,'>>',$error_log) or die "Not able to open error log file: $error_log\n\n===========================================================================================================\n\n";
	return( $artifactoryLogDir );
}

##############################################################################################################
# write output only to the console
#
sub write_console
{
	print @_;
}

##############################################################################################################
# write output to console and complete log
#
sub write_complete_log
{
	my ($message, $verbose_mode) = @_;
	$verbose_mode //= 1;
	print $message if ($verbose_mode);
	print COMPLETE_LOG $message;
}

##############################################################################################################
# write output to console, complete log and error log
#
sub write_error_log
{
	my ($message, $verbose_mode) = @_;
	$verbose_mode //= 1;
	print $message if ($verbose_mode);
	print COMPLETE_LOG $message;
	print ERROR_LOG $message;
}

##############################################################################################################
# write log into stdout, complete and error log based on user selection ( not used )
#
sub write_log
{
	my ($write_string,$select_handler) = @_;
	my @output_handler = ();
	@output_handler = ('STDOUT') if ($select_handler == 0);
	@output_handler = ('COMPLETE_LOG','STDOUT') if ($select_handler == 1);
	@output_handler = ('ERROR_LOG','STDOUT') if ($select_handler == 2);
	@output_handler = ('COMPLETE_LOG','ERROR_LOG','STDOUT',) if ($select_handler == 3);
	
	foreach (@output_handler)
	{
		select $_;
		print $write_string;
	}	
}

#################################################################################################################
# Normalise path from unix, window path and also from relative, canonical path (remove unnecessary slashes also) : story-52831
#
sub normalise_path
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
	if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i)
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
# generate hash checksums for specified HashAlgorithm in windows: feature-76330
#
sub get_hash_value
{
	my ($hash_algo, $file_path) = @_;
	my %algo = ('MD5' => 'md5sum', 'SHA1' => 'sha1sum');

	if ($^O =~ /cygwin/i || $^O =~ /linux/i )
	{
		$file_path =~ s/ /\\ /ig;	
		my $cmd = "$algo{$hash_algo} $file_path";
		my $cmd_output = readpipe($cmd);
		my @hash_data = split / /, $cmd_output;
		my $hash_code = $hash_data[0];
		return $hash_code;
	}
	else
	{
		return digest_file_hex($file_path, $hash_algo);		
	}
}

#################################################################################################################
## get the file size in bytes from server
##
#sub get_file_size
#{
#	my ($server, $userId, $password, $repo, $artifact) = @_;
#	my $value = "";
#	my $cmd = "curl -u $userId:$password --silent --head --location ";
#	   $cmd .= "\"$server/$repo/$artifact\" ";
#	my $result = `$cmd`;
#	my @resultvalues = split(/\n/, $result);
#
#	foreach my $line (@resultvalues)
#	{
#	   if ($line =~ /Content-Length/)
#	   {
#	      $line =~ s/[^0-9]//g;
#	      $value = $line;
#	   }
#	}
#
#	return $value;
#}

#################################################################################################################
# get md5 checksum value for requested files from artifactory
#
sub get_server_generated_md5_checksum_value
{
	my ($server, $userId, $password, $noproxy, $repo, $artifact) = @_;
	my $md5ChecksumValue = "";
    my $cmd = set_curl_command($noproxy, $userId, $password, 0);
    $cmd .= "--silent --head --location \"$server/$repo/$artifact\"";	   
	   
	my $result = `$cmd`;
	my @resultvalues = split(/\n/, $result);

	foreach my $line (@resultvalues)
	{
	   if ($line =~ /X-Checksum-Md5/)
	   {
	      my @checksumcontent = split(/:/, $line);
	      $md5ChecksumValue = $checksumcontent[1];
	      $md5ChecksumValue =~ s/^\s+|\s+$//g;
	   }
	}

	return $md5ChecksumValue;
}

#################################################################################################################
# retrieve password if operating system is windows: feature-76330
#
sub get_win_password
{
	my ($password) = @_;
	use Term::ReadKey;
	ReadMode 'noecho';
	$password = ReadLine 0;
	chomp $password;
	ReadMode 'normal'; 
	return $password
}

#################################################################################################################
# retrieve version of artifactory instance: story-165111
#
sub get_artifactory_version
{
	my ($server, $noproxy) = @_;
    my $cmd = set_curl_command($noproxy, "", "", 0);
	$cmd .= "-s -X GET \"$server/api/system/version\" ";
	my $jsonOutput = `$cmd`;
	my $decodedJsonOutput = decode_json($jsonOutput);
	my $artifactoryVersion = sprintf("%.2f", $$decodedJsonOutput{'version'});
	return $artifactoryVersion
}

#################################################################################################################
# retrieve latest script version from artifactory server
#
sub get_latest_script_version
{
	my ($server, $userId, $password, $noproxy) = @_;	
    my $cmd = set_curl_command($noproxy, $userId, $password, 0);
    $cmd .= "-s -S -X GET \"$server/api/storage/cmmtg-tools/artifactory/latestversion/?properties=version\"";	

	my $jsonOutput = `$cmd`;
	my $decodedJsonOutput = decode_json($jsonOutput);
	my $propeties = $$decodedJsonOutput{'properties'};
	my $latestScriptVersion = sprintf("%.2f", $$propeties{'version'}[0]);
	return $latestScriptVersion
}

#################################################################################################################
# returns current script version
#
sub check_script_version
{
	return $scriptVersion
}

#################################################################################################################
# process repository owner details
#
sub get_repository_owner_details
{
	my ($server, $userId, $password, $repo_name, $noproxy) = @_;

    my $prop_cmd = set_curl_command($noproxy, $userId, $password, 0);
    $prop_cmd .= "-sS -X GET \"$server/api/storage/$repo_name?properties\"";
	my $get_prop = `$prop_cmd`;
	my $repo_properties = decode_json($get_prop);

	if (defined $repo_properties ->{"properties"} && defined $repo_properties ->{"properties"}{"repositoryowner"})
	{
		my $repo_owner = $repo_properties ->{"properties"}{"repositoryowner"}[0]; 
		my $mail = MIME::Lite->new(
				'From'          => 'Briefkasten.CMToolgroup@de.bosch.com',
				'To'            => $repo_owner,
				'Subject'       => "Artifactory Client Script Usage Alert - Autogenerated",
				'Type' 			=> 'text/plain',
				'Data' 			=> "Hi,\n\nUser $userId is using an older version of script to access $repo_name repository in $server. ".
								   "You are receiving this email because you are the repository owner of $repo_name.".
								   "This is an autogenerated mail. Reply to this mail will not be answered. Please ".
								   "ignore if this mail is not relevant to you."
    			)or die "Error creating container. $!\n";
    	$mail->send('smtp','rb-smtp-int.bosch.com');
    	write_error_log("INFO: An email has been sent to repository owner to notify the usage of older version of scripts.\n");
	}
	else
	{
		my $mail = MIME::Lite->new(
				'From'          => 'Briefkasten.CMToolgroup@de.bosch.com',
				'To'            => 'Service-Inquiry.CIBEEArtifactory@de.bosch.com',
				'Cc'      		=> 'Sounak.Patra@in.bosch.com',
				'Subject'       => "Artifactory Client Script Usage Alert - Autogenerated",
				'Type' 			=> 'text/plain',
				'Data' 			=> "Hi,\n\nrepositoryowner property is not set for repository $repo_name in $server. ".
								   "Please set the property. This is an autogenerated mail."
    			)or die "Error creating container. $!\n";
    	$mail->send('smtp','rb-smtp-int.bosch.com');
    	write_error_log("INFO: An email has been sent to admins to update the repository owner.\n");
	}	
}

#################################################################################################################
# process repository details
#
sub get_repository_details
{
	my ($server, $userId, $password, $repo_name, $noproxy) = @_;
	
    my $cmd = set_curl_command($noproxy, $userId, $password, 0);
    $cmd .= "-sS -X GET \"$server/api/repositories\"";
	my $artifactory_config = `$cmd`;
	my $decoded_config = decode_json($artifactory_config);

  	foreach (@$decoded_config)
  	{
  		if ($_->{"key"} eq $repo_name)
  		{
  			if (lc $_->{"type"} eq "local")
  			{
  				get_repository_owner_details($server, $userId, $password, $repo_name, $noproxy)
  			}
  		}
  	}
}

#################################################################################################################
# validates the script version
#
sub validate_script_version
{
	my ($server, $userId, $password, $repo_name, $noproxy) = @_;
	my $script_version = check_script_version();
	my $latest_script_version = get_latest_script_version($server, $userId, $password, $noproxy);
	my $local_time = localtime;

	write_error_log("TIME STAMP	: $local_time\nScript Version\t: $script_version\n");

	if (sprintf("%.2f", $script_version) < $latest_script_version)
	{
		write_error_log("!! WARNING: You are using an older version. Please get the latest script from $server/cmmtg-tools/artifactory/latestversion/userScripts !!\n");
		write_error_log("\nINFO: Script execution will be stopped. Please proceed with the latest version of scripts.\n");
		get_repository_details($server, $userId, $password, $repo_name, $noproxy);
		exit(1);
	}
}

#################################################################################################################
# reads the specified file: story-178336
#
sub read_file
{
	my ($file_name) = @_;
	my $error_msg = "Not able to open " . "$file_name\n";
	open(FILE_READ, "<$file_name") || die $error_msg;
	my @lines = <FILE_READ>;
	close(FILE_READ);
	
	return @lines
}

#################################################################################################################
# writes data to the specified file: story-178336
#
sub write_to_file
{
	my ($file_name, @data) = @_;
	my $error_msg = "Not able to open " . "$file_name\n";	
	open(FILE_WRITE, ">$file_name") || die $error_msg;
	print FILE_WRITE @data;
	close(FILE_WRITE);
}

#################################################################################################################
# generates/updates md5 value of the downloaded files in _content.md5 file: story-178336
#
sub generate_md5_file
{
    my ($md5_file_list_ref, $files_ref, $content_md5_file) = @_;
    # Dereferencing and copying each array
    my @md5_file_list = @{ $md5_file_list_ref };
    my @files = @{ $files_ref };

  	if (scalar @md5_file_list != 0)
  	{
  		if (-e $content_md5_file)
  		{
  			# Read the file
			my @lines = read_file($content_md5_file);
			# Removes the current file names from array
			foreach my $new_file (@files)
			{
				my $index = 0;
				foreach(@lines)
				{
					my $ext_file_name = (split / \*./, $_)[1];
					my $new_file_name = "/" . $new_file;
					# Trimming white space from both end of the file names
					$ext_file_name =~ s/^\s+|\s+$//g;
					$new_file_name =~ s/^\s+|\s+$//g;
					# Deletes the new file registry from _content.md5 file if any
					if ($ext_file_name eq $new_file_name)
					{
						delete $lines[$index];
					}
					$index++;
				}
			}
			# Updates the array with new MD5 values
			foreach(@md5_file_list)
			{
				push (@lines, $_);
			}
			# Writes MD5 value to _content_md5_file
			write_to_file($content_md5_file, @lines);
  		}
  		else
  		{
			write_to_file($content_md5_file, @md5_file_list);
  		}
  	}
}

#################################################################################################################
# update list of file names with failed md5 validation in _content_error.md5 file
#
sub generate_md5_error_file
{
	my ($md5_error_file_list_ref, $content_md5_error_file) = @_;
	my @md5_error_file_list = @{ $md5_error_file_list_ref };
	my $len_error_file_list = scalar @md5_error_file_list;
	if ($len_error_file_list != 0)
	{
		unlink($content_md5_error_file);
		write_to_file($content_md5_error_file, @md5_error_file_list);
	}
}

#################################################################################################################
# generate the percentage value for downloading and uploading files - feature : 76327
#
sub get_progress_percentage
{
	my ($percentage_value, $message, $total_no_of_versions, $current_version_number) = @_;
	$percentage_value = $percentage_value. (" " x (4 - length($percentage_value))). "%";
	my $current_progress = ("[ ". $current_version_number. (" " x (length($total_no_of_versions) - length($current_version_number))). "/". $total_no_of_versions. " ]") if ($total_no_of_versions);
	my $percentage_progress = $message. " Progress: ". $percentage_value;
	   $percentage_progress = ($message. " Progress ". $current_progress. ": ". $percentage_value) if $total_no_of_versions;
	   
	print ($percentage_progress);
	print ("\b" x length($percentage_progress)); 	
}

#################################################################################################################
# download certificate file from artifactory - story: 246847
#
sub download_certificate_file
{
	my ($server, $userId, $password, $certificate_name, $current_certificate_path, $noproxy, @cert_files) = @_;

    my $cmd = set_curl_command($noproxy, $userId, $password, 0);
    $cmd .= "-s -f -L --write-out \"%{http_code}\" \"$server/cmmtg-tools/certificates/$certificate_name\" -o \"$current_certificate_path\"";
	my $result = `$cmd`;

	if ($? eq "0") 
	{
		my $digit = (split //, $result)[0];
		if ($digit == 4)
		{
            my $err_msg = parse_curl_error_output($result);
            if ($err_msg ne "")
            {
                print "ERROR MESSAGE: $err_msg\n";
            }
			print "ERROR: Can't download the certificate file. Please download it manually. Abort...";
			exit(1);
		}
		else
		{
			foreach my $i(0 .. $#cert_files)
			{
				unlink $cert_files[$i];
			}
		}
	}
	else
	{
        my $err_msg = parse_curl_error_output($result);
        if ($err_msg ne "")
        {
            print "ERROR MESSAGE: $err_msg\n";
        }
        print "ERROR: Can't download the certificate file. Please download it maually. Abort...";
		exit(1);
	}	
}

#################################################################################################################
# update ssl certificates - story: 246847
#
sub update_ca_certificates
{	
	my ($server, $userId, $password, $no_proxy) = @_;	
	$server =~ s/https:/http:/ig;
	$server =~ s/.com/.com:8081/ig;
	my $certificate_name = "curl-ca-bundle.crt";
    my @cert_files;

	if ($^O =~ /mswin/i)
	{
	  	my $curl_path_cmd =  "where curl";
	  	my $curl_path = `$curl_path_cmd`;
    	my $base_name = dirname($curl_path);

    	my $current_certificate_path = catfile($base_name, $certificate_name);
		my $copy_certificate_path = catfile($base_name, "curl-ca-bundle_copy.crt");	

		move $current_certificate_path, $copy_certificate_path;
		push @cert_files, $copy_certificate_path;
		download_certificate_file($server, $userId, $password, $certificate_name, $current_certificate_path, $no_proxy, @cert_files);
	}
	elsif ($^O =~ /cygwin/i)
	{
		my $cygwin_path_cmd =  "cygpath -m /usr/";
		my $cygwin_path = `$cygwin_path_cmd`;
		my $base_name = dirname($cygwin_path);

		my $ca_bundle_certificate_path = catfile($base_name, "ssl/certs/ca-bundle.crt");
		my $ca_bundle_trust_certificate_path = catfile($base_name, "ssl/certs/ca-bundle.trust.crt");
		my $ca_curl_certificate_path = catfile($base_name, "ssl/certs/$certificate_name");

		my $ca_bundle_certificate_copy_path = catfile($base_name, "ssl/certs/ca-bundle_copy.crt");
		my $ca_bundle_trust_certificate_copy_path = catfile($base_name, "ssl/certs/ca-bundle_copy.trust.crt");
		my $ca_curl_certificate_copy_path = catfile($base_name, "ssl/certs/curl-ca-bundle_copy.crt");

		move $ca_bundle_certificate_path, $ca_bundle_certificate_copy_path;
		move $ca_bundle_trust_certificate_path, $ca_bundle_trust_certificate_copy_path;
		move $ca_curl_certificate_path, $ca_curl_certificate_copy_path;

		push @cert_files, $ca_bundle_certificate_copy_path;
		push @cert_files, $ca_bundle_trust_certificate_copy_path;
		push @cert_files, $ca_curl_certificate_copy_path;

		download_certificate_file($server, $userId, $password, $certificate_name, $ca_curl_certificate_path, $no_proxy, @cert_files);

		copy $ca_curl_certificate_path, $ca_bundle_certificate_path;
		copy $ca_curl_certificate_path, $ca_bundle_trust_certificate_path;
	}
	elsif ($^O =~ /linux/i)
	{
		system("sudo bash $Bin/Certificates/certdeploy.sh");
	}
	elsif ($^O =~ /darwin/i)
	{
		system("sudo bash $Bin/Certificates/mac_cert_update.sh");
	}
}

#################################################################################################################
# ping artifactory instance for https connection check and update ssl certificate if required - story: 246847
#
sub check_https
{
	my ($server, $userId, $password, $noproxy) = @_;
	
    my $check_https_status_cmd = set_curl_command($noproxy, "", "", 1);
    $check_https_status_cmd .= "-s \"$server/api/system/ping\"";	
  	my $check_https_status = `$check_https_status_cmd`;

  	if ( $check_https_status !~ /^ok$/i )
  	{
  		write_error_log("\nERROR: SSL certificate verification failed\nUpdating certificate...\n");
  		update_ca_certificates($server, $userId, $password, $noproxy);
  	}
  	
  	if (ping_server($server, $noproxy))
  	{
  		write_error_log("\nERROR: SSL certificate update failed. Please update the certificate manually. Abort...");
  		write_error_log("\nPlease follow the steps in https://inside-docupedia.bosch.com/confluence/x/wAkpG to update ssl certificate manually");
  		exit(1);
  	}
}

#################################################################################################################
# check if server can be contacted and repository exist is given server : story-52831
#
sub check_settings
{
	my ($serverReceived, $userIdReceived, $passwordReceived, $repoToCheck, $noproxy) = @_ ;
	my $repoFoundFlag = 0;
	my $writeString ;

    my $getRepoCmd = set_curl_command($noproxy, $userIdReceived, $passwordReceived, 1);
    $getRepoCmd .= "-s -S -X GET \"$serverReceived/api/repositories\"";
  	my $result = `$getRepoCmd`;

  	if( $result =~ /^$/ || $result =~ /errors/i )
  	{
  		unless ( $result =~ /^$/ )
  		{
  			$result 			=~ /.*"message"\s*:\s*\"(.*)\"/i;
  			$writeString 		= "\nMESSAGE : $1 \n" ;
  		}
  		$writeString	   .= "ERROR   : Could not contact artifactory server: $serverReceived for user: $userIdReceived\n\n";
    	$writeString	   .= "\n===========================================================================================================\n\n";
    	write_error_log( $writeString );
    	exit(1);
  	}
	if ( $repoToCheck )
	{
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
	}
	return(0);
}

#################################################################################################################
# Asks for user password to override .artifactory config file
#
sub get_password
{
    my $password = "";
    print "\nPassword not specified in command line, Do you want you enter password (y|n): ";
    my $input 	= <STDIN>;
    if ( $input =~ /^(Y|y|yes)$/i)    
    {
        print "Enter Password : ";
        if ($^O =~ /linux/i || $^O =~ /cygwin/i || $^O =~ /darwin/i)
        {
            system('stty -echo');  # Disable echoing
            chomp($password = <STDIN>);
            system('stty echo');   # Turn it back on	
        }
        elsif ($^O =~ /mswin/i)
        { 
            $password = get_win_password($password)
        }
        print "\n\n";
				
        if ($password eq "")
        {
            write_error_log("\nERROR: Entered empty password\n");
            write_error_log("\n===========================================================================================================\n\n");
            exit(1);                
        }
		
		return $password;
    }
    else
    {
        write_complete_log( "INFO: Abort...\n");
        exit(0);                
    }
}

1;
# EOF - LOAD OK