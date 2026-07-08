#!/usr/bin/perl
#################################################################################################################################
# FILE			:   certificate.pl																								#
#																																#
# DESCRIPTION	: 	Check and copy ssl certificate for artifactory servers														#
#																																#
# USAGE			:	perl certificate.pl																			             	#
#																																#
# COPYRIGHT		:   (c) 2015 Robert Bosch GmbH																					#
# HISTORY		:																												#
#																																#
# Date         	| Author                 		| Modification																	#
# 27.05.2016   	| Saddam hussain A 	(RBEI/ECA2)	| Initial version																#
#################################################################################################################################	
# add the private includepathes
use FindBin qw($Bin $Script);
use lib $Bin."/modules";
use lib $Bin;
use File::Basename;
use strict;
use Getopt::Long;

my $user			= '';
my $password		= '';
my $linuxCertPath 	= '/etc/ssl/certs';
my $redhatCertPath	= '';
my $windowsCertPath	= '';
my $certificateName	= 'Bosch-CA1-DE_150512_pem.crt';

scanArgs();

if ( $^O =~ /linux/i ) #&& !( -f "$linuxCertPath/$certificateName" )
{
	my $sourceCertificatePath 	= "$Bin/Certificates";
	my $destinationCertificatePath 	= "/usr/local/share/ca-certificates";
	if ( -f "$sourceCertificatePath/$certificateName" )
	{
		my $cmd = "sudo -S cp \'$sourceCertificatePath/$certificateName\' $destinationCertificatePath";
		$cmd = " echo $password | " . $cmd if ( $password ); 
		print "$cmd\n";		
		`$cmd` ;
		if ( $? )
		{
			print "\nERROR: Not able to copy certificate to location: /usr/local/share/ca-certificates\nMessage: $!\n";
			#print "\narray - $@ , quesiton - $?, exclamatory - $!\n";
		}
		else
		{
			print "\nINFO: Successfully copied certifacte to location: /usr/local/share/ca-certificates\n\n";
			#print "\narray - $@ , quesiton - $?, exclamatory - $!\n";
		 	my $cmd = "sudo -S update-ca-certificates";
		 	$cmd = " echo $password | " . $cmd if ( $password );
		 	
			my $result = ` $cmd`;
			if ( $result =~ /^done/i || $result !~ /permission denied/i )
			{
				print "$result\nINFO: Successfully updated the certificates to $linuxCertPath\n\n";
			}
			else
			{
				print "ERROR: Failed to update the certifactes\nMessage: $result\n"
			}
		}
	}
	else
	{
		print "ERROR: Source certificate: $Bin/Certificates/$certificateName not available\n";
	}
}

#################################################################################################################
# 										 ALL FUNCTIONS DEFINITION												#
#################################################################################################################
#
# Scan  input parameter
sub scanArgs
{
	GetOptions(
  				'p=s'			=> \$password,
  			  )
}
