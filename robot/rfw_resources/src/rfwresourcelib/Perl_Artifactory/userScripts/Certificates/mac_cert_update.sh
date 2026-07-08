#!/usr/bin/env bash -eu

set -eu

function add_crt_macos()
{
   CRT=$1
   wget -O ${TMPDIR}/${CRT} http://sgpvmc0127.apac.bosch.com/config-4/CA-certs/${CRT} 2>/dev/null||echo "crt download failed"
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ${TMPDIR}/${CRT} 2>/dev/null
   sudo security add-trusted-cert -d -r trustAsRoot -k /Library/Keychains/System.keychain ${TMPDIR}/${CRT} 2>/dev/null||:
   rm ${TMPDIR}/${CRT};
}

if sudo -n true 2>/dev/null; then
   :
else
   echo $0" requires sudo, please enter" && sudo echo
fi

add_crt_macos Bosch-CA-DE.crt
add_crt_macos Bosch-CA1-DE.crt
add_crt_macos Bosch-CA2-DE.crt
add_crt_macos BoschInternetProxyCA2.crt
add_crt_macos ProxyHTTP.crt
