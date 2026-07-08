#!/bin/bash
# -*- coding: utf-8 -*-

###########################################################################################
#
#                       certdeploy.sh
#
# Created by Gnyanraj Laxman Kognoor(Kognoor.GnyanrajLaxman@in.bosch.com)
# Copyright Robert Bosch Car Multimedia GmbH 2021. All rights reserved.
#
#
#Usage			:
#Example: certdeploy.sh
#
#
#HISTORY	                                                                        #
# Date         	| Author                 		    | Modification		#
# 28.01.2021   	| Gnyanraj Laxman Kognoor   		| To fix the SSL Certificate issues	
#
###########################################################################################

# Reinstalling the bosch-ca-certificates
result=$(apt-get install --reinstall bosch-ca-certificates) ||
    { rc=$?; echo "error installing bosch-ca-certificates:"; echo "${result}"; exit $rc; }>&2
echo "Updated the SSL Certificates Successfully on machine `hostname`."

# remove old entries from /etc/ca-certificates.conf
sed -i '/Bosch-CA-DE.crt/d' /etc/ca-certificates.conf
sed -i '/Bosch-CA1-DE.crt/d' /etc/ca-certificates.conf
sed -i '/Bosch-CA2-DE.crt/d' /etc/ca-certificates.conf
sed -i '/BoschInternetProxyCA2.crt/d' /etc/ca-certificates.conf
sed -i '/ProxyHTTP.crt/d' /etc/ca-certificates.conf

# Soft link /usr/local/share/ca-certificates to /usr/share/ca-certificates
cd /usr/local/share/ca-certificates
ln -sf /usr/share/ca-certificates/Bosch-CA-DE.crt Bosch-CA-DE.crt
ln -sf /usr/share/ca-certificates/Bosch-CA1-DE.crt Bosch-CA1-DE.crt
ln -sf /usr/share/ca-certificates/Bosch-CA2-DE.crt Bosch-CA2-DE.crt
ln -sf /usr/share/ca-certificates/BoschInternetProxyCA2.crt BoschInternetProxyCA2.crt
ln -sf /usr/share/ca-certificates/ProxyHTTP.crt ProxyHTTP.crt

update-ca-certificates
