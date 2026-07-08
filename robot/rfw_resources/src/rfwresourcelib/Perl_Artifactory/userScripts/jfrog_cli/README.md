# CLI for JFrog Artifactory

## Installation
`curl -fL http://getcli.jfrog.io | sh` or [CLI Download](https://www.jfrog.com/getcli/)
### Linux
```
sudo cp ./jfrog /usr/local/bin/
sudo chmod ga+x /usr/local/bin/jfrog
```

## Configuration
### Authentication

`./jfrog rt config --url http://rb-cmbinex-hi-p1.de.bosch.com:8081/artifactory --user sor2hi`
> API key (leave empty for basic authentication):

Get API key from https://rb-cmbinex-hi-p1.de.bosch.com/artifactory/webapp/#/profile after login

The API key can also be retrieved via REST API:
`curl -s X GET -u sor2hi:password_or_encrypted_password "http://rb-cmbinex-hi-p1.de.bosch.com:8081/artifactory/api/security/apiKey"`

### Bosch SSL Certificates
Currently not required as we use http instead of https.

Otherwise check [Using Self-signed SSL Certificates](https://www.jfrog.com/confluence/display/CLI/CLI+for+JFrog+Artifactory#CLIforJFrogArtifactory-UsingSelf-signedSSLCertificates).

`cp di_misc_tools/tools/artifactory/Certificates/Bosch-CA1-DE_150512_pem.crt ~/.jfrog/security/`

## Usage
[CLI for JFrog Artifactory usage](https://www.jfrog.com/confluence/display/CLI/CLI+for+JFrog+Artifactory)


#### Search
`jfrog rt s "sw-navi-snapshot/navi-sdk/rnaivi/winsim/debug/*version.txt"`

#### Download single file

`jfrog rt dl "sw-navi-snapshot/navi-sdk/rnaivi/winsim/debug/nav17.01_stabi_2017.06.2/version.txt"`

Destination is `./navi-sdk/rnaivi/winsim/debug/nav17.01_stabi_2017.06.2/version.txt`

#### Download whole dir

`jfrog rt dl "sw-navi-snapshot/navi-sdk/rnaivi/winsim/debug/nav17.01_stabi_2017.06.2/" down/`

Destination is `./down/navi-sdk/rnaivi/winsim/debug/nav17.01_stabi_2017.06.2/`

##### Download whole dir without leading source path
`./artifactory_download.py sw-navi-snapshot/navi-sdk/rnaivi/winsim/debug/nav_int_2018.05.3/ z:/sdk/gen3_rnaivi/Navigation/`

### Tests
```
rm -rf /tmp/test_down_perl && time perl ../download_artifact.pl --verbose -d -r nav-data-repos -c DATA-STORE/Bosch/EUR/A-IVI-Mid-Renault_2016.03_2.4.3_DEUEUR_R1/r1/DATA/ -o /tmp/test_down_perl
Total no. of files: 98, downloaded: 98, failed: 0
Time taken: 0 hour 1 minute 51 second

Refer log files for more details
Download log       : /home/vagrant/Artifactory_log/download.log
Error log          : /home/vagrant/Artifactory_log/download_error.log

===========================================================================================================


real	1m51.123s
user	0m4.128s
sys	0m30.508s
```


```
rm -rf /tmp/test_down_cli && time jfrog rt dl --split-count=15 --threads=15 "nav-data-repos/DATA-STORE/Bosch/EUR/A-IVI-Mid-Renault_2016.03_2.4.3_DEUEUR_R1/r1/DATA/" /tmp/test_down_cli/
[Info] Downloaded 98 artifacts.

real	1m16.351s
user	0m2.912s
sys	0m51.332s
```
