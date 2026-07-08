use FindBin qw($Bin $Script);
use lib $Bin;
use artifactory_config;
use Getopt::Long;

my $rootComponent, $fileWithoutSpace;
#my $md5_value_server = "0";
scanArgs();
my  ( $server, $userId, $password, $no_proxy ) = read_from_config();
#print "$server, $no_proxy\n$rootComponent\n$fileWithoutSpace\n";

my $md5_value_server = get_server_generated_md5_checksum_value( $server, $userId, $password, $no_proxy, $rootComponent, $fileWithoutSpace);

print "$fileWithoutSpace MD5: $md5_value_server\n";
exit 0;



sub scanArgs
{
  my $res = GetOptions (
  'i=s'    => \$fileWithoutSpace,
  'r=s'    => \$rootComponent,
  ) or do {
    write_error_log("\nERROR: Extra or unknown arguments passed, check the usage.\n");
    displayUsage('all_arguments');
    write_error_log("\n===========================================================================================================\n\n");
    exit(1);
    };
}
