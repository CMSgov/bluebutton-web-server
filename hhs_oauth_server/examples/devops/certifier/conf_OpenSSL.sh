#!/usr/bin/env bash
# Update the openssl.conf file

# get default openssl.cnf
# Edit default_ca setting to BB_CA_Default

# write BB_CA_Default section
echo "Creating KeyStore folders"
mkdir -p $OW_SPACE_BASE/CA
mkdir -p $OW_SPACE_BASE/CA/certs
mkdir -p $OW_SPACE_BASE/CA/crl
mkdir -p $OW_SPACE_BASE/CA/newcerts
mkdir -p $OW_SPACE_BASE/CA/private
touch $OW_SPACE_BASE/CA/database.txt
echo "01" >$OW_SPACE_BASE/CA/serial
export OW_TGT_OSSLCONF=$OW_SPACE_BASE/openssl.conf
export OW_OCONF=$OW_SPACE_BASE/input/openssl_conf_add.txt
echo " " >$OW_OCONF
# echo "############################################################################ " >$OW_OCONF
# echo "[ ca ] " >>$OW_OCONF
# echo "default_ca      = BB_CA_Default            # BlueButton  default ca section " >>$OW_OCONF
# echo " " >>$OW_OCONF
echo "Writing BB_CA_Default settings in $OW_OCONF"
echo "############################################################################" >>$OW_OCONF
echo "[ BB_CA_Default ] " >>$OW_OCONF
echo " " >> $OW_OCONF
echo "dir             = $OW_SPACE_BASE/CA            # Where everything is kept " >>$OW_OCONF
echo "certs           = \$dir/certs            # Where the issued certs are kept " >>$OW_OCONF
echo "crl_dir         = \$dir/crl              # Where the issued crl are kept " >>$OW_OCONF
echo "database        = \$dir/database.txt        # database index file. " >>$OW_OCONF
echo "#unique_subject = no                    # Set to 'no' to allow creation of " >>$OW_OCONF
echo "                                        # several ctificates with same subject. " >>$OW_OCONF
echo "new_certs_dir   = \$dir/newcerts         # default place for new certs. " >>$OW_OCONF
echo " " >>$OW_OCONF
echo "certificate     = \$dir/cacert.pem       # The CA certificate " >>$OW_OCONF
echo "serial          = \$dir/serial           # The current serial number " >>$OW_OCONF
echo "crlnumber       = \$dir/crlnumber        # the current crl number " >>$OW_OCONF
echo "                                        # must be commented out to leave a V1 CRL " >>$OW_OCONF
echo "crl             = \$dir/crl.pem          # The current CRL " >>$OW_OCONF
echo "private_key     = \$dir/private/cakey.pem # The private key " >>$OW_OCONF
echo "RANDFILE        = \$dir/private/.rand    # private random number file " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "x509_extensions = usr_cert              # The extentions to add to the cert " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "# Comment out the following two lines for the "traditional " >>$OW_OCONF
echo " # (and highly broken) format. " >>$OW_OCONF
echo "name_opt        = ca_default            # Subject Name options " >>$OW_OCONF
echo "cert_opt        = ca_default            # Certificate field options " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "# Extension copying option: use with caution. " >>$OW_OCONF
echo "# copy_extensions = copy " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "# Extensions to add to a CRL. Note: Netscape communicator chokes on V2 CRLs " >>$OW_OCONF
echo "# so this is commented out by default to leave a V1 CRL. " >>$OW_OCONF
echo "# crlnumber must also be commented out to leave a V1 CRL. " >>$OW_OCONF
echo "# crl_extensions	= crl_ext " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "default_days	= 3650			# how long to certify for " >>$OW_OCONF
echo "default_crl_days= 30			# how long before next CRL " >>$OW_OCONF
echo "default_md	= default		# use public key default MD " >>$OW_OCONF
echo "preserve	= no			# keep passed DN ordering " >>$OW_OCONF
echo "  " >>$OW_OCONF
echo "# A few difference way of specifying how similar the request should look " >>$OW_OCONF
echo "# For type CA, the listed attributes must be the same, and the optional " >>$OW_OCONF
echo "# and supplied fields are just that :-) " >>$OW_OCONF
echo "policy		= policy_anything " >>$OW_OCONF
echo " " >>$OW_OCONF

echo "Updating $OW_TGT_OSSLCONF"
# replace default_ca setting
sed -i 's@= CA_default@= BB_CA_Default@' $OW_TGT_OSSLCONF
# Append new default_ca settings to openssl.conf
cat $OW_OCONF >>$OW_TGT_OSSLCONF
echo "openssl.conf Update completed."
