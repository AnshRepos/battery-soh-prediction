#########################################################################################################################################################################################################
#																																																		#			
# FILE			:  artifact_properties.pl																																								#
#																																																		#
# DESCRIPTION	:  Show or attach or delete properties (file/folder)																																	#
#																																																		#
# USAGE			:  perl artifact_properties.pl [ -h ] ( -m | -d ) -r <repo> ( -c <component> |( -g <groupId> -a <artifactId> -v <versionId>) ( ( -set <property=value> | -setc <configFilePath> ) |		#
#				   		( (  -show | -delete ) <property> ) | ( ( -showc | -deletec ) <configFilePath> ) ) [ -o <outputFile> ] [ -rec ] [ -f ] [ -s <server> -u <userId> -p <password>				    #
#                       -useproxy ]                                                                                                                                                                     #
#																																																		#
# ARGUMENTS		:  see Usage																																											#																			
#																																																		#
# COPYRIGHT		:  (c) 2014 Robert Bosch GmbH																																							#
# HISTORY		:																																														#
#																																																		#
# Date         	| Author                		| 	Modification																																		#
# 14.11.2014   	| M.Schoenfelder (ext)  		| 	Initial version																																		#
# 22.06.2015   	| M.Schoenfelder (ext)  		| 	adapt to new config file																															#
# 04.01.2016   	| Saddam hussain A (RBEI/ECA2)	| 	JSON decoder used to parse json output from artifactory rest api : story-46175																		#
#										  			Path normalisation : story-46175																													#
#										  			Arguments check added : story-46175																													#
#										  			Logger file adaption, delete property function added to delete property : story-47348																#
#										  			Input parameter modified for delete property : story-46175																							#
#										  			Delete property adapted : story-46175																												#
#										  			Operation based helper message added : story-47348																									#
# 13.01.2016	| Saddam hussain A (RBEI/ECA2)	| 	Maven and generic layout adapted : story-47991																										#
#										  			Maven and generic argument check functions added : story-47991 																						#
# 01.03.2016	| Saddam hussain A (RBEI/ECA2)	| 	Adapt to new config file ( check settings, normalise path function)	: story-52829																	#
# 09.02.2017	| Sounak Patra (RBEI/ECA2)		|   Modified code to handle empty line with spaces in config file					 																	#
# 30.06.2017	| Sounak Patra (RBEI/ECA2)      | 	Made modifications to check latest script version and set properties based on artifactory version: story-165111										#
# 25.10.2017	| Sounak Patra (RBEI/ECA2)		|   Added feature to stop execution of older scripts: story-185699                                                                                      #
# 20.03.2019	| Sounak Patra (RBEI/ECQ2)		|   Added noproxy option in curl                                                                                                                        #
# 02.08.2019	| Sounak Patra (RBEI/ECQ2)		|   Removed bug from  164 line                                                                                                                          #
#																																												                        #
#########################################################################################################################################################################################################
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use artifactory_config;
use strict;
use Getopt::Long;
use Cwd;
use Data::Dumper;
use JSON qw( decode_json );
use XML::Simple;

# Usage
my $usageParameter;
my $usage = 
{
	'header'			=>	'Usage:',
	'prefixArguments' 	=> "perl $0",
	'allArguments' 		=> '[ -h ] ( -m | -d ) -r <repo> ( -c <component> |( -g <groupId> -a <artifactId> -v <versionId>) ( ( -set <property=value> | -setc <configFilePath> ) | 
		( ( -show | -delete ) <property> ) | ( ( -showc | -deletec ) <configFilePath> ) ) [ -o <outputFile> ] [ -rec ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'mavenArguments'		=> '[ -h ] -r <repo> -g <groupId> -a <artifactId> -v <versionId> ( ( -set <property=value> | -setc <configFilePath> ) | 
		( ( -show | -delete ) <property> ) | ( ( -showc | -deletec ) <configFilePath> ) ) [ -o <outputFile> ] [ -rec ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',
	'genericArguments'		=> '[ -h ] -r <repo> -c <component> ( ( -set <property=value> | -setc <configFilePath> ) | 
		( ( -show | -delete ) <property> ) | ( ( -showc | -deletec ) <configFilePath> ) ) [ -o <outputFile> ] [ -rec ] [ -f ] [ -s <server> -u <userId> -p <password> -useproxy ]',

	'content' 			=> 'Show/Set/Delete properties of a file/folder.',

	'description' 		=>
		{  
			'1'  => { '-h'    	=>  '-h                         : Print this usage text.',},
			'2'  => { '-m' 		=>  '-m        <maven>          : For maven repository layout',},
    		'3'  => { '-d' 		=>  '-d        <generic>        : For generic repository layout'},
    		'4'  => { '-r'    	=>  '-r        <repo>           : Artifactory repository'},
    		'5'  => { '-c'    	=>  '-c        <component>      : file/folder name (relative path to repository mentioned in -r), applicable for generic layout'},
    		'6'  => { '-g' 		=>  '-g        <groupId>        : GroupId, applicable for maven layout, use together with -a & -v'},
    		'7'  => { '-a' 		=>  '-a        <artifactId>     : ArtifactId, applicable for maven layout, use together with -g & -v'},
    		'8'  => { '-v' 		=>  '-v        <versionId>      : VersionId, applicable for maven layout, use together with -g & -a'},
    		'9'	 => { '-show' 	=>  '-show     <property>       : Property to be shown, use "all" to show all properties'},
    	   '10'  => { '-showc'	=>  '-showc    <configFilePath> : Configuration file name, refer below example'},
    	   '11'	 => { '-delete' =>  '-delete   <property>       : Property to be deleted, use "all" to delete all properties'},
    	   '12'  => { '-deletec'=>  '-deletec  <configFilePath> : Configuration file name, refer below example'},
    	   '13'	 => { '-set'  	=>  '-set      <property=value> : Property and value to be set'},
    	   '14'  => { '-setc'	=>  '-setc     <configFilePath> : Configuration file name, refer below example'},
    	   '15'  => { '-rec'  	=>  '-rec      <recursive>      : Recursive set or delete properties (has no effect on show properties)'},
    	   '16'  => { '-o'      =>  '-o        <outputFile>     : File name to export output content'},
    	   '17'  => { '-f'    	=>  '-f        <force>          : Force delete artifact property without confirmation (has not effect in show and set property)'},
    	   '18'  => { '-s'    	=>  '-s        <server>         : Artifactory Server (optional, will override config file)'},
    	   '19'  => { '-u'    	=>  '-u        <userId>         : Artifactory User ID (optional, will override config file)'},
    	   '20'  => { '-p'    	=>  '-p        <password>       : Artifactory Password (optional, will override config file)'},
    	   '21'  => { '-useproxy' =>  '-useproxy                  : Uses current proxy settings (optional, will override config file)'}
		},
    'endContent' => "e.g.: -set, -show and -delete argument pattern to pass as inputs to the script
    		perl $0 -set property1=value1,value2;property2=value3
    		perl $0 -show property1,property2 	or perl $0 -show all
    		perl $0 -delete property1,property2 or perl $0 -delete all
    
    Other arguments will be ignored when using -setc or -showc or -deletec (configFile)
    	
    	Format of <configFile>:
				# used with comments
				# one line per action; items seperated by two colon; all arguments are mandatory
				repository::component::property1=value1,value2;property2=value3,value4 				if set property and generic repository layout
				repository::groupId::artifactId::versionId::property1=value1,value2;property2=value3,value4 	if set property and maven repository layout
				repository::component::property1,property2								if show or delete property and generic repository layout
				repository::groupId::artifactId::versionId::property1,property2						if show or delete property and maven repository layout
       	
				When using optional arguments like server, user_id, password the settings from .artifactory config file will be overwritten!",
};
# arguments
my ( $server, $userId, $password, $repository_name, $no_proxy );
my ( $maven, $generic, $recursive, $force, $outFile, @keyValuePair );

#other arguments
my ($setFlag, $showFlag, $deleteFlag, $errorString);
my $auto_answer   			= $ENV{_SET_ENV_AUTO_ANSWER};
my $mavenArgumentCount		= 5;
my $genericArgumentCount	= 3;
my @argumentList			= ();
my $dev_nul 				= "/dev/null";
my $propertiesLogFile      	= 'properties.log';
my $errorLogFile         	= 'properties_error.log';
   
# Create log file
my $artifactoryLogDir = create_log_file( $propertiesLogFile,$errorLogFile );
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

if ($setFlag)
{	write_error_log("On Server\t: $server\nOperation\t: Set properties\n\n");; }
elsif ($deleteFlag)
{	($force) ? ( write_error_log("On Server\t: $server\nOperation\t: Delete properties( force )\n\n") ) :
										( write_error_log("On Server\t: $server\nOperation\t: Delete properties( non-force )\n\n") ); }
else
{	
	write_error_log("On Server\t: $server\nOperation\t: Show properties\n\n");
	if ($outFile)
	{ 
		$outFile = normalise_path($outFile);
		if ( $outFile == 1 )
		{
			write_error_log("\nERROR: Invalid output file: $outFile to export artifact and its property, export will not be done!\n\n");
		}
		else
		{
			open (SHOWOUT ,">$outFile") or  
  						do 	{
  								write_error_log("$!\nWARNING: Not able to open output file: $outFile to export artifact and its property, export will not be done!\n\n") 
							}
		} 
	}
	else
	{	write_complete_log("\nINFO: Output File not specified, Artifact-Property list export will not be done\n\n")	}
}

NEXT : foreach my $inputFeedHashRef (@argumentList)
{
	# Exit if server is not pingable(It will be replaced with ping api from Artifactory version 4.2.0)
	if( check_settings( $server, $userId, $password, $$inputFeedHashRef{repo}, $no_proxy ))
	{
		my	$writeString		= "\nERROR: Repository not found or user not having read permission to ";
  			$writeString 	   .= "repository: $$inputFeedHashRef{repo} in artifactory server: $server\n\n";
    	write_error_log($writeString);
    	$errorString           .= $writeString;
		next NEXT; 
	}
	
	next NEXT if( $maven && validVersionCheck($$inputFeedHashRef{repo}.'/'.$$inputFeedHashRef{targetPath}) );
	# Show and set properties	
	my $artifactory_version = get_artifactory_version($server, $no_proxy);
	my $artifact_properties  = $$inputFeedHashRef{properties};
	if ($artifactory_version >= 5.0)
	{
			$artifact_properties =~ tr/|/;/;	
	}
	
	if ($setFlag)
	{	setProps($$inputFeedHashRef{repo},$$inputFeedHashRef{targetPath},$artifact_properties ) ; }
	elsif ($deleteFlag)
	{	deleteProps($$inputFeedHashRef{repo},$$inputFeedHashRef{targetPath},$$inputFeedHashRef{properties} ); }
	else
	{	showProps($$inputFeedHashRef{repo},$$inputFeedHashRef{targetPath},$$inputFeedHashRef{properties} ); }
}

close SHOWOUT;

# Check for intermediate errors and exit
if ($errorString ne "") 
{
	my $writeString  = "";
  	   $writeString .= "\nFollowing problems occured during script execution:\n";
  	   $writeString .= "-----------------------------------------------------\n";
  	   $writeString .= "$errorString\n";
  	write_error_log($writeString);
	print "\nRefer log files for more details \nProperties log\t: $artifactoryLogDir$propertiesLogFile\n"; 
	print "Error log\t: $artifactoryLogDir$errorLogFile\n";
  	write_error_log("\n===========================================================================================================\n\n");
  	exit(1);
}
else 
{
	print "\nRefer log files for more details \nProperties log\t: $artifactoryLogDir$propertiesLogFile\n"; 
	print "Error log\t: $artifactoryLogDir$errorLogFile\n";
	write_error_log("\n===========================================================================================================\n\n");
  	exit(0);
}

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Display usage : story-47348
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
# show properties
#
sub showProps
{
	my ($repo, $artifact, $showProps) = @_;
 	my ($writeString, $nonExistentProperty);
  	$showProps= '' if ($showProps eq 'all');
	
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    $cmd .= "-sS -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.ItemProperties+json\" \"$server/api/storage/$repo/$artifact?properties\=$showProps\"";
  	my $output = `$cmd`;

	$showProps= 'all' unless ($showProps);
  	my $decodeJson = decode_json($output) ;

  	# Example output for setting property
  	if (defined $decodeJson->{errors} ) 
  	{
  		write_error_log("Show properties( $showProps ) for artifact: $repo/$artifact - $$decodeJson{errors}[0]{status} - ERROR\n");
  		$errorString .= "Failed to show artifact: $repo/$artifact properties - $$decodeJson{errors}[0]{status} - Message : $$decodeJson{errors}[0]{message}\n";
  	}
  	else
  	{
  		print SHOWOUT "$server/api/storage/$repo/$artifact :";
  		write_complete_log("Show properties( $showProps ) for artifact: $repo/$artifact");
  		if ($showProps ne 'all')
  		{
            my $showAllCmd = set_curl_command($no_proxy, $userId, $password, 0);
  			$showAllCmd .= "-sS -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.ItemProperties+json\" \"$server/api/storage/$repo/$artifact?properties\" ";
  			my $showAllCmdOutput = `$showAllCmd`;
  			my $decodeJsonShowAllCmdOutput = decode_json($showAllCmdOutput);

  			foreach my $property (split(',',$showProps))
		 	{
				$nonExistentProperty   .= "$property," unless ($$decodeJsonShowAllCmdOutput{properties}{$property} ) ;
		 	} 
		 	$nonExistentProperty	    =~ s/\,$//;	
		 	write_complete_log("\t(Property: \"$nonExistentProperty\" not exist)") if ($nonExistentProperty); 		#Display properties which are not available in artifact
  		}
  		
  		foreach my $property (keys %{$$decodeJson{properties}})
  		{
  			if (@{$$decodeJson{properties}{$property}}[0]) 
  			{
  				$writeString .= "\n\t$property:  @{$$decodeJson{properties}{$property}}";
  				print SHOWOUT "\n\t$property:  @{$$decodeJson{properties}{$property}}"
  			}
  			else
  			{
  				$writeString .= "\n\t$property :  -";
  				print SHOWOUT "\n\t$property :  -";
  			}
  		}
  		$writeString     .= "\n";
  		print SHOWOUT "\n\n----------------------------------------------------------------------------------------------------------------------\n\n";
  	}
  	write_complete_log("$writeString\n");
}	

#################################################################################################################
# set properties
#
sub setProps
{
	my ($repo, $artifact, $setProps) = @_;
	my $nonExistentProperty;
  	#$setProps =~ s#;#\|#; 															# replace semicolon with pipe
  	($recursive) ? ($setProps .= "&recursive=1") : ($setProps .= "&recursive=0");   # otherwise artifactory default recursive used
	
    my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
    $cmd .= "-sS -X PUT \"$server/api/storage/$repo/$artifact?properties=$setProps\"";
  	my $output = `$cmd`;

  	if ($output)
  	{
  		my $decodeJson = decode_json($output);
  		if (defined $decodeJson->{'errors'} )
  		{
  			write_error_log("Set properties( $setProps ) for artifact: $repo/$artifact - $$decodeJson{errors}[0]{status} - ERROR\n");
  			$errorString .= "Failed to set artifact: $repo/$artifact properties - $$decodeJson{errors}[0]{status} - Message : $$decodeJson{errors}[0]{message}\n";
  		}
  	}
  	else 
  	{
        my $cmd = set_curl_command($no_proxy, $userId, $password, 0);
        $cmd .= "-sS -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.ItemProperties+json\" \"$server/api/storage/$repo/$artifact?properties\" ";
  		my $output = `$cmd`;
  		my $decodeJson = decode_json($output) ;
  		my $nonExistentPropertyCount = 0;

  		foreach my $keyValue ( @keyValuePair )
		{
			$keyValue =~ /\=/;
			my ( $property,$value ) 	= ( $`, $' );
			unless ( defined $$decodeJson{properties}{$property} )
			{
				$nonExistentProperty .= "$property,";
				$nonExistentPropertyCount++;
			}
		} 
		if ( $nonExistentProperty )
		{
			if (  ( scalar @keyValuePair ) == $nonExistentPropertyCount )
			{
				write_complete_log("Set properties( $setProps ) for artifact: $repo/$artifact - Failed \n");
			}
			else
			{
				write_complete_log("Set properties( $setProps ) for artifact: $repo/$artifact - Partial \t(Property: \"$nonExistentProperty\" not set)\n");
			}
		}
		else
		{
			write_complete_log("Set properties( $setProps ) for artifact: $repo/$artifact - Ok\n");
		}
  	}
}

#################################################################################################################
# delete properties : story-46175
#
sub deleteProps
{
	my ($repo, $artifact, $deleteProps) = @_;
  	my ($writeString,$nonExistentProperty,$displayAll);
	($recursive) ? ($deleteProps .= "&recursive=1") : ($deleteProps .= "&recursive=0");   # otherwise artifactory default recursive used  
  	if(! $force)
	{
		write_complete_log("\nDo you want to delete artifact: $repo/$artifact properties: $deleteProps (y|n):");
		if(<STDIN> =~ /^(Y|y|yes)$/i)
		{
			write_complete_log("\t\tProceeding to $artifact - ");
		}
		else
		{
			write_complete_log("Delete artifact property - Skipped \n");
			return;
		}
	}
	$deleteProps 	= '' if ($deleteProps eq 'all' ) ;
    my $showCmd = set_curl_command($no_proxy, $userId, $password, 0);
  	$showCmd .= "-sS -X GET -H \"Content-Type: application/vnd.org.jfrog.artifactory.storage.ItemProperties+json\" \"$server/api/storage/$repo/$artifact?properties\=$deleteProps\" ";
  	my  $showOutput = `$showCmd`;
  	my $showOutputDecodeJson = decode_json($showOutput) ;

  	# Example output for setting property
  	if (defined $showOutputDecodeJson->{errors} ) 
  	{
  		write_error_log("Delete properties( $deleteProps ) of artifact: $repo/$artifact - $$showOutputDecodeJson{errors}[0]{status} - ERROR\n");
  		$errorString .= "Failed to delete artifact: $artifact properties - $$showOutputDecodeJson{errors}[0]{status} - Message : $$showOutputDecodeJson{errors}[0]{message}\n";
  	}
  	else
  	{
		unless ( $deleteProps ) 
		{
			foreach (keys %{$$showOutputDecodeJson{properties}})
			{	
				($deleteProps = join(',',$_,$deleteProps) )	# for deleting all properties, getting list of available properties by above show property command
			}
		}
		else
		{	
			my $splitDeleteProps = $deleteProps;
			   $splitDeleteProps =~ s/(&recursive\=[0|1])$//;
			foreach my $property (split ',',$splitDeleteProps)
			{
				$nonExistentProperty .= "$property," unless ($$showOutputDecodeJson{properties}{$property} ) ;
		 	} 
		}
  		$deleteProps =~ s/\,\&recursive/\&recursive/;				 # remove extra comma between property and recursive 
  		$nonExistentProperty =~ s/\,$//;							 # remove extra comma at the end

        my $deleteCmd = set_curl_command($no_proxy, $userId, $password, 0);
        $deleteCmd .= "-sS -X DELETE \"$server/api/storage/$repo/$artifact?properties\=$deleteProps\" ";
  		my $output = `$deleteCmd`;

  		if ($output)
  		{
  			my $decodeJson 				= decode_json($output) ;
  			if (defined $decodeJson->{'errors'} )
  			{
  				write_error_log("Delete properties( $deleteProps ) of artifact: $repo/$artifact - $$decodeJson{errors}[0]{status} - ERROR\n");
    			$errorString .= "Failed to delete artifact: $artifact properties - $$decodeJson{errors}[0]{status} - Message : $$decodeJson{errors}[0]{message}\n";
  			}
  		}
  		else 
  		{
  			write_complete_log("Delete properties( $deleteProps ) of artifact: $repo/$artifact");
    		($nonExistentProperty) ? (write_complete_log(" - ok (Property: \"$nonExistentProperty\" not exist) \n") ) : (write_complete_log(" - ok \n") );
  		}
  	}	
}  	

#################################################################################################################
# check if version is valid by checking the maven-metadata.xml : story-47991
#
sub validVersionCheck
{
	my $versionPath 			= shift;
	$versionPath				=~ /(.+)\/(.+)/;
	my ($artifactPath,$version) = ($1,$2);

	my $mavenMetaXmlCmd = set_curl_command($no_proxy, $userId, $password, 0);
    $mavenMetaXmlCmd .= "-sS \"$server/$artifactPath/maven-metadata\.xml\"";
    my $mavenMetaXml = `$mavenMetaXmlCmd`;
	#my $mavenMetaXml = `curl --noproxy \"$no_proxy\" -sS -u $userId:$password \"$server/$artifactPath/maven-metadata\.xml\"`;

  	if ($mavenMetaXml =~ /errors.+\"status\".+404/s ) 
	{
		write_error_log("ERROR: Failed to validate version (groupId or artifactId or version may be invalid or given version not available in maven-metadata\.xml)!\n\n");
		$errorString .= "ERROR: Failed to validate version (groupId or artifactId or version may be invalid or given version not available in maven-metadata\.xml)!\n\n"; 
		return(1);	
	}
	else
	{
		my $xmlRef	= XMLin($mavenMetaXml);
		my %versionHash;
		if (ref $$xmlRef{versioning}{versions}{version} eq 'ARRAY')
		{
			%versionHash = map {$_ => 1} @{$$xmlRef{versioning}{versions}{version}};
		}
		else
		{
			$versionHash{$$xmlRef{versioning}{versions}{version}} = 1;
		}
		#print Dumper \%versionHash;
		unless ( $versionHash{$version} )
		{
			write_error_log("ERROR: Failed to validate version (versionId not valid or not exist)!\n\n");
			$errorString .= "ERROR: Failed to validate version (versionId not valid or not exist)!\n\n";
			return(1);
		}
	}
	return (0);
}
##################################################################################################################
# scan arguments and assign them to global script variables
# show help text if arguments are not set correctly
#
sub scanArgs
{
  	my ($h, $repo, $component, $groupId, $artifactId, $versionId, $showConfigFile, $deleteConfigFile, 
        $setConfigFile, $setProps, $showProps, $deleteProps, $configFile, $targetPath, $useproxy);  
  									
  	my $res = GetOptions (
  						'h'     		=> \$h,
     					'f'	  			=> \$force,
     					'rec'    		=> \$recursive,
   						'u=s'    		=> \$userId,
   						'p=s'    		=> \$password,
   						's=s'    		=> \$server,
   						'm'				=> \$maven,
     					'd'				=> \$generic,
   						'r=s'    		=> \$repo,
   						'g=s'			=> \$groupId,
   						'a=s'			=> \$artifactId,
   						'v=s'			=> \$versionId,
   						'c=s'    		=> \$component,
   						'o=s'       	=> \$outFile,
   						'set=s'		 	=> \$setProps,
   						'setc=s'  		=> \$setConfigFile,
   						'show=s'		=> \$showProps,
   						'showc=s'   	=> \$showConfigFile,
   						'delete=s'	 	=> \$deleteProps,
   						'deletec=s' 	=> \$deleteConfigFile,
                        'useproxy'      => \$useproxy,
  						)or do {
  							write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
  							displayUsage('allArguments');
							write_error_log("\n===========================================================================================================\n\n");
							exit(1);
  			    		};

	$repository_name = $repo;
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
	# check for operation type, always any one operation can be performed( when more than one operation or no operation specified, will exit)
  	my $commandLineArgumentCount 	= 0;
  	$commandLineArgumentCount++ if ($setProps);
  	$commandLineArgumentCount++ if ($showProps);
  	$commandLineArgumentCount++ if ($deleteProps);
  	
  	$commandLineArgumentCount++ if $deleteConfigFile;
  	$commandLineArgumentCount++ if $showConfigFile;
  	$commandLineArgumentCount++ if $setConfigFile;
  	
  	if ($commandLineArgumentCount == 0 )
  	{
  		write_error_log("\nERROR: Arguments missing!\nOperation type should be given in the arguments as (-set|setc for setting property or -show|showc for showing property or -delete|deletec for deleting property)\n");
		($maven) ? ( displayUsage('mavenArguments') ) : ( displayUsage('genericArguments') );
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
  	}
  	if ($commandLineArgumentCount > 1)
  	{
  		write_error_log("\nERROR: Extra argument, any one operation ( -set|setc or show|showc or -delete|deltec) can be selected\n");
		($maven) ? ( displayUsage('mavenArguments') ) : ( displayUsage('genericArguments') );
		write_error_log("\n===========================================================================================================\n\n");
		exit(1);
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
  	
  	# to display specific helper for set or show or delete operation( this usage hash will used by dispalyUsage function )
  	($maven) ? ( $usageParameter = '-g <groupId> -a <artifactId> -v <versionId>' ) : ( $usageParameter = '-c <component>' ) ;
  	if ( $setConfigFile || $setProps )
  	{
  		$setFlag					= "1" ;
		$$usage{'setArguments'}		= "[ -h ] -r <repo> $usageParameter ( -set <property=value> | -setc <configFilePath> ) [ -rec ] [ -f ] [ -s <server>] [ -u <userId> -p <password>]";
  	}
  	elsif ( $deleteConfigFile || $deleteProps )
  	{
  		$deleteFlag 				= '1' ;
  		$$usage{'deleteArguments'}	= "[ -h ] -r <repo> $usageParameter ( -delete <property> | -deletec <configFilePath> ) [ -rec ] [ -f ] [ -s <server>] [ -u <userId> -p <password>]";
  	}
  	else
  	{
  		$showFlag 					= '1' ;
  		$$usage{'showArguments'}	= "[ -h ] -r <repo> $usageParameter ( -show <property> | -showc <configFilePath> ) [ -o <outputFile> ] [ -s <server>] [ -u <userId> -p <password>]";
  	}
	
	$configFile = $setConfigFile || $deleteConfigFile || $showConfigFile ;
  	if ($configFile)
  	{
  		# check other arguments, if given will be omitted as all arguments are replaced by inputs from config file
  		if ($repo || $groupId || $artifactId || $versionId || $component)
  		{
  			write_complete_log("\nWARNING: Other arguments will be ignored when reading from config file\n\n");
  		}
  		$configFile = normalise_path($configFile);
  		if ($configFile == 1)
  		{
  			write_error_log("\nERROR: Invalid config file: $configFile path!\n");
			displayUsage('showArguments') 		if ($showFlag);
			displayUsage('setArguments') 		if ($setFlag);
			displayUsage('deleteArguments') 	if ($deleteFlag);
  			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
  		}
  		#print "$configFile\n";
    	if ((! -e $configFile) || (! -f $configFile))
    	{
    		write_error_log("\nERROR: config file: $configFile not exist or not a file!\n");
			displayUsage('showArguments') 		if ($showFlag);
			displayUsage('setArguments') 		if ($setFlag);
			displayUsage('deleteArguments') 	if ($deleteFlag);
			write_error_log("\n===========================================================================================================\n\n");
  			exit(1);
    	}
    	open(CONFIG, "<$configFile") or do	{	write_error_log("Message: $!\nERROR: Not able to open config file: $configFile!\n");
    											write_error_log("\n===========================================================================================================\n\n");
    											exit(1);
    										};
    	my @lines = <CONFIG>;
    	close(CONFIG);
    	if ($setFlag)
    	{
    		if (readArgumentsFromConfig(@lines) )
      		{
      			displayUsage('setArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
    	}
      	elsif ($deleteFlag)
      	{
      	    if (readArgumentsFromConfig(@lines) )
      		{
      			displayUsage('deleteArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
      	}
      	else
      	{
      		if (readArgumentsFromConfig(@lines) )
      		{
      			displayUsage('showArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
    	}
  	}
  	else
  	{
  		#print "set $setFlag shw $showFlag delete $deleteFlag\n";
  		my ($inputFeed, $argCheckResult );
  	    if ($setFlag)
      	{
      		($argCheckResult,$inputFeed) = argumentCheck($repo, $groupId, $artifactId, $versionId, $component, $setProps);
      		if ($argCheckResult)
      		{
      			write_error_log("!\n");
      			displayUsage('setArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
      	}
      	elsif ($deleteFlag)
      	{
      		($argCheckResult,$inputFeed) = argumentCheck($repo, $groupId, $artifactId, $versionId, $component, $deleteProps);
      		if ($argCheckResult)
      		{
      			write_error_log("!\n");
      			displayUsage('deleteArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
      	}
      	else
      	{
      		($argCheckResult,$inputFeed) = argumentCheck($repo, $groupId, $artifactId, $versionId, $component, $showProps);
      		if ($argCheckResult)
      		{
      			write_error_log("!\n");
      			displayUsage('showArguments');
				write_error_log("\n===========================================================================================================\n\n");
				exit(1);
      		}
      	}
      	push (@argumentList,$inputFeed );
  	}  	
}

#################################################################################################################
# Read from config file : story-47991
#
sub readArgumentsFromConfig
{
	my @lines = 	@_ ;
	my $lineCount 	= 	0;
	foreach my $line (@lines)
    {
    	$lineCount++;
    	next if ($line =~ /#/ || $line =~ /^$/ || $line =~ /^\s*$/); 	# ignore comments and empty lines
    	chomp $line;
    	my ($cfgRepo,$cfgGroupId,$cfgArtifactId,$cfgVersionId,$cfgComponent,$cfgProps);
    	my $cfgExtraArgumentFlag = 0;
    	if ($maven)
    	{	
    		my $argCount = ($cfgRepo,$cfgGroupId,$cfgArtifactId,$cfgVersionId,$cfgProps) = split /::/, $line ;
      		$cfgExtraArgumentFlag = 1 if ($argCount > $mavenArgumentCount )	
      	}
      	else
      	{  	
      		my $argCount = ($cfgRepo,$cfgComponent,$cfgProps) = split /::/, $line;	
			$cfgExtraArgumentFlag = 1 if ($argCount > $genericArgumentCount )	
      	}
      	
      	if ( $cfgExtraArgumentFlag == 1 )
      	{
  			write_error_log("\nERROR: Extra argument in config file at line $lineCount!\n");
			return (1);
      	}
      	my ($argCheckResult,$inputFeed) = argumentCheck($cfgRepo,$cfgGroupId,$cfgArtifactId,$cfgVersionId,$cfgComponent,$cfgProps);
      	$repository_name = $cfgRepo;
      	
      	if ($argCheckResult)
      	{
      		write_error_log(" at line $lineCount!\n\n");
      		return (1);
      	}
      	push (@argumentList,$inputFeed );
	}
	
	return (0);
}

#################################################################################################################
# Call maven or generic argument check function : story-47991
#
sub argumentCheck
{
	my ($repo,$groupId,$artifactId,$versionId,$component,$property) = @_;
	my ($targetPath, %inputFeed);
	if (!$repo) 
  	{
  		write_error_log("\nERROR: Repository missing");
    	return (1);
  	}
  	if (!$property)
  	{
  		write_error_log("\nERROR: Property missing");
    	return (1);
  	}
  	#print "repo $repo group $groupId art $artifactId version $versionId com $component pro $property\n";
	if ($maven)
    {
    	if (!$groupId || !$artifactId || !$versionId)
    	{
    		write_error_log("\nERROR: Argument missing");
    		return (1);
    	}
    	if ($component)
    	{
    		write_error_log("\nERROR: Extra argument");
    		return (1);
    	}
    	
    	if(mavenArgumentCheck(\$repo, \$groupId, \$artifactId, \$versionId, \$property ))
    	{	return(1); 	}
      	else
      	{	$targetPath = $groupId.'/'.$artifactId.'/'.$versionId; 	}
	}
    else
    {
    	if (!$component)
    	{
    		write_error_log("\nERROR: Argument missing");
    		return (1);
    	}
    	if ($groupId || $artifactId || $versionId)
    	{
    		write_error_log("\nERROR: Extra argument");
    		return (1);
    	}
    	
    	if (genericArgumentCheck(\$repo, \$component, \$property ))
    	{	return(1);	}
    	else
    	{	$targetPath = $component;  	}
    }
    $inputFeed{repo}       		= $repo;
    $inputFeed{properties} 		= $property;
    $inputFeed{targetPath}  	= $targetPath;
    #print Dumper \%inputFeed;
    return (0,\%inputFeed) ;
}

#################################################################################################################
# check generic arguments are passed correctly : story-47991
# 
sub genericArgumentCheck
{
	my ($repo,$component,$property,$outFile) = @_;
	
  	  		$$component 	=~ s#\\#\/#g;
  	1 while $$component 	=~ s#^(\\|\/)##g;
  	1 while $$component 	=~ s#(\\|\/)$##g;
  	1 while $$component 	=~ s#\\\\|\/\/#\/#g;
	
	$$property 				=~ s#^\s+##;
	$$property 				=~ s#\s+$##;
    $$property 				=~ s#,\s+#,#g;
    $$property 				=~ s#\s+,#,#g;											# remove unwanted space in between in property;
    $$property 				=~ s#;\s+#;#g;
    $$property 				=~ s#\s+;#;#g;
    $$property 				=~ s#=\s+#=#g;
    $$property 				=~ s#\s+=#=#g;
	#print "prop $$property\n";
	return (1)	if ($setFlag && setArgumentConsistencyCheck($property) );
	
	$$property				=~ s#\s#%20#g;
	$$repo     				=~ s#^\s+##;
	$$repo		     		=~ s#\s+$##;
	$$component 			=~ s#^\s+##;
	$$component 			=~ s#\s+$##;
	 $outFile  				=~ s#^\s+##;
	 $outFile		  		=~ s#\s+$##;
	
  	return (0);
}
#################################################################################################################
# check generic arguments are passed correctly : story-47991
# 
sub mavenArgumentCheck
{
	my ($repo,$groupId,$artifactId,$versionId,$property,$outFile) = @_;
	if ( $$artifactId =~ /(\\|\/)/ || $$versionId =~ /(\\|\/)/ ) 
  	{
  		write_error_log("\nERROR: Invalid Artifact id or Version");
    	return (1);
  	}

  	  		$$groupId 		=~ s#\\#\/#g;
  	1 while $$groupId 		=~ s#^(\\|\/)##g;
  	1 while $$groupId 		=~ s#(\\|\/)$##g;
  	1 while $$groupId 		=~ s#\\\\|\/\/#\/#g;
 
#	    $$property  	  		=~ s#(,|;)$##g;
#	    $$property				=~ s#^(,|;)##g;											# remove extra commas|semicolon at the begining and end
#	    $$property  	  		=~ s#,;#;#g;
#	    $$property	 			=~ s#;,#;#g;
#	    1 while ($$property 	=~ s#,,#,#g);
#	    1 while ($$property 	=~ s#;;#;#g);
	$$property 				=~ s#^\s+##;
	$$property 				=~ s#\s+$##;
    $$property 				=~ s#,\s+#,#g;
    $$property		 		=~ s#\s+,#,#g;											# remove unwanted space in between in property;
    $$property 				=~ s#;\s+#;#g;
    $$property		 		=~ s#\s+;#;#g;
    $$property 				=~ s#=\s+#=#g;
    $$property		 		=~ s#\s+=#=#g; 
 	
	return (1)	if ($setFlag && setArgumentConsistencyCheck($property));

	$$property				=~ s#\s#%20#g;
	$$repo     				=~ s#^\s+##;
	$$repo		     		=~ s#\s+$##;
	$$groupId 				=~ s#^\s+##;
	$$groupId		 		=~ s#\s+$##;
	$$artifactId			=~ s#^\s+##;
	$$artifactId			=~ s#\s+$##;
	$$versionId				=~ s#^\s+##;
	$$versionId 			=~ s#\s+$##;
	 $outFile  				=~ s#^\s+##;
	 $outFile  				=~ s#\s+$##;
	 
	
  	return (0);
}

#################################################################################################################
# Set argument property consistency check : story-47991
#
sub setArgumentConsistencyCheck
{
	my $property = shift;
	my $index =0;
	my %keyValuePair ;
	foreach ( split '\;', $$property )					# separate each key value pair based on semicolon
	{
		$keyValuePair{$index} = $_;
		$index++;
	}
	$$property	= '';
	foreach my $key ( sort {$a <=> $b} keys %keyValuePair )
	{
		#print "$key\n";
		if ( $keyValuePair{$key} 	=~ /\\$/ )
		{
			$keyValuePair{$key+1} 	= "$keyValuePair{$key}\;$keyValuePair{$key+1}";				# join back and delete separations having back slash(\), which meant they are not separate value but to specify special character
			delete $keyValuePair{$key};
		} 
	}
	push @keyValuePair,$keyValuePair{$_}  foreach (sort {$a <=> $b} keys %keyValuePair);
	
	foreach my $keyValuePair ( @keyValuePair )																
	{
		if ($keyValuePair 	!~ /^[\w_]/ )					# invalidate if not starts with character or _
		{						  			
			write_error_log("\nERROR: Invalid Property ( property name cannot be blank or contain spaces & special characters )");
			return(1);
		}
		if ( $keyValuePair	=~ /\=/ && $` !~ /\\$/ )					
		{
			my $key 		= $`;
			my $value		= $';
			foreach my $keyCharacter ( split //, $key )
			{
				if ( $keyCharacter !~ /[\w\d\-_.]/ )				# invalidate if contains character other than listed
				{
					write_error_log("\nERROR: Invalid Property key ( property name cannot be blank or contain spaces & special characters )");
					return(1);
				}
			}
			#print "key $key value $value\n";
			while (1)
			{	# invalidate if contains special character other than listed
				if ( ( $value =~ /\|/ && $` !~ /\\$/ ) || ( $value =~ /=/ && $` !~ /\\$/ ) ) #|| ( $value =~ /\,/ && $` !~ /\\$/ ) )
				{ 
					#print "match is $` last $'\n";
					write_error_log("\nERROR: Invalid Property ( special characters should be escaped by backslash '\\' )");
					return(1);
				}
				else
				{
					( $value eq $' ) ? ( last ) : ( $value = $' );
				}
			}
#			if ($value =~ /.*?=/ && $value !~ /\\=/ )
#			{
#				write_error_log("\nERROR: Invalid Property");
#				return(1);
#			}
#			if ($key eq 'retention.RetDate' && $value !~ /^2[0-1]\d\d-([0-1]?\d)-([0-3]\d)$/ && $1 <= 12 && $2 <= 31 )
#			{
#				write_error_log("\nERROR: Invalid retention.Retdate property(yyyy-mm-dd) or One date can be set");
#				return(1);
#			}
#			if ($key eq 'retention.RetC'  && $value !~ /^[0-4]$/ )
#			{
#				write_error_log("\nERROR: Invalid retention class(retention.RetC should be [0-4])");
#				return(1);
#			}
		}
		else
		{
			write_error_log("\nERROR: Invalid Property (Property cannot be empty or when having empty value for property name, it should have '='(eg: key=) )");
			return(1);
		}
		$$property = join( '|', $$property, $keyValuePair);
	}
	$$property	=~ s#^\|##;
	$$property 	=~ s#\|$##;
	#print "prop : $$property\n";
	return(0);
}
