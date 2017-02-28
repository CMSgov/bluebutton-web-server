#!/usr/bin/env bash
export OW_CERT_LOG=/home/ec2-user/build_Certs.log
echo "Building Certs with OpenSSL" >$OW_CERT_LOG
date >>$OW_CERT_LOG
openssl version >>$OW_CERT_LOG
export OW_SPACE_BASE=/home/ec2-user/test2/OpenSSL/workspace
echo "Create OpenSSL Workspace" >>$OW_CERT_LOG
echo "Workspace Base: $OW_SPACE_BASE " >>$OW_CERT_LOG
mkdir -p $OW_SPACE_BASE
# Move to $OW_SPACE_BASE
cd $OW_SPACE_BASE
mkdir -p $OW_SPACE_BASE/Keys
mkdir -p $OW_SPACE_BASE/CSR
mkdir -p $OW_SPACE_BASE/Certificates
mkdir -p $OW_SPACE_BASE/input
echo "01" >$OW_SPACE_BASE/serial.txt
touch $OW_SPACE_BASE/database.txt
echo "Created sub-directories:" >>$OW_CERT_LOG
# Setup openssl.conf
# touch $OW_SPACE_BASE/openssl.conf

cp /etc/pki/tls/openssl.cnf $OW_SPACE_BASE/openssl.conf

# Run script to update openssl.conf
/home/ec2-user/conf_OpenSSL.sh
echo "-----------------------------"
echo "Installed OpenSSL.conf" >>$OW_CERT_LOG
export OW_CERT_IN=$OW_SPACE_BASE/input/cert_input.txt
echo "Certificate input will be input from $OW_CERT_IN" >>$OW_CERT_LOG
# Setup Certificate input to pipe to commands
echo "US" >$OW_CERT_IN
echo "Maryland" >>$OW_CERT_IN
echo "Baltimore" >>$OW_CERT_IN
echo "Centers for Medicare and Medicaid Services" >>$OW_CERT_IN
echo "BlueButton API" >>$OW_CERT_IN
echo "BlueButtonOnFHIRAPI" >>$OW_CERT_IN
echo "mark.scrimshire@cms.hhs.gov" >>$OW_CERT_IN
echo "." >>$OW_CERT_IN
echo "." >>$OW_CERT_IN
echo "." >>$OW_CERT_IN
echo "." >>$OW_CERT_IN
echo "." >>$OW_CERT_IN
echo "Certificate Settings: " >>$OW_CERT_LOG
cat $OW_CERT_IN >>$OW_CERT_LOG
echo "-----------------------------" >>$OW_CERT_LOG
export OW_STORE_IN=$OW_SPACE_BASE/input/store_input.txt
echo "Store input will be input from $OW_STORE_IN" >>$OW_CERT_LOG
# Setup KeyStore input to pipe to commands

# What is your first and last name?
echo "BlueButtonOnFHIR API" >$OW_STORE_IN
# What is the name of your organizational unit?
echo "OEDA" >>$OW_STORE_IN
# What is the name of your organization?
echo "Centers for Medicare and Medicaid Services" >>$OW_STORE_IN
# What is the name of your City or Locality?"
echo "Baltimore" >>$OW_STORE_IN
# What is the name of your State or Province?
echo "Maryland" >>$OW_STORE_IN
# What is the two-letter country code for this unit?
echo "US" >>$OW_STORE_IN
# Is CN=BlueButtonOnFHIR API, OU=OEDA, O=Centers for Medicare and Medicaid Services, L=Baltimore, ST=Maryland, C=US correct?
echo "yes" >>$OW_STORE_IN
# Enter key password for <server>
#	(RETURN if same as keystore password):
echo " " >>$OW_STORE_IN
echo "Store Input: " >>$OW_CERT_LOG
cat $OW_STORE_IN >>$OW_CERT_LOG
echo "-----------------------------" >>$OW_CERT_LOG
echo "Trust Input: " >>$OW_CERT_LOG
export OW_TRUST_IN=$OW_SPACE_BASE/input/trust_input.txt
echo "yes" >$OW_TRUST_IN
cat $OW_TRUST_IN >>$OW_CERT_LOG
echo "-----------------------------" >>$OW_CERT_LOG
echo "CSR Input:" >>$OW_CERT_LOG
export OW_CSR_IN=$OW_SPACE_BASE/input/csr_input.txt
echo "-----------------------------" >>$OW_CERT_LOG
# Setup CSR input to pipe to commands
echo "US" >$OW_CSR_IN
echo "Maryland" >>$OW_CSR_IN
echo "Baltimore" >>$OW_CSR_IN
echo "Centers for Medicare and Medicaid Services" >>$OW_CSR_IN
echo "BlueButton API" >>$OW_CSR_IN
echo "BlueButtonOnFHIRAPI" >>$OW_CSR_IN
echo "mark.scrimshire@cms.hhs.gov" >>$OW_CSR_IN

# Generate a random passphrase (<20 Chars)
# openssl rand 10 -base64 -out $OW_SPACE_BASE/input/random.txt
# Testing with a fixed RANDOM value
echo "T0Psecret" >$OW_SPACE_BASE/input/random.txt

# Used for CSR Challenge Password and to add to Root Cert Passphrase
cat $OW_SPACE_BASE/input/random.txt >>$OW_CSR_IN
echo "CMS" >>$OW_CSR_IN

# Setup Root Cert Passphrase
# This is also needed for CSR Creation
export OW_ROOT_CA=$OW_SPACE_BASE/Keys/BlueButtonRootCA.key
# echo "BlueButton0nFHIR_is_$(cat $OW_SPACE_BASE/input/random.txt)_Awesome" >$OW_SPACE_BASE/input/passphrase.txt
# testing with fixed value for passphrase
echo "BlueButton$(cat $OW_SPACE_BASE/input/random.txt)" >$OW_SPACE_BASE/input/passphrase.txt

# Append passphrase to CSR input
cat $OW_SPACE_BASE/input/passphrase.txt >>$OW_CSR_IN

ls -l $OW_SPACE_BASE >>$OW_CERT_LOG
ls -l $OW_SPACE_BASE/input >>$OW_CERT_LOG
# Generate the Root Certificate
# create the Root Certificate

openssl genrsa -des3 -out $OW_ROOT_CA -passout file:$OW_SPACE_BASE/input/passphrase.txt 2048
echo "Root Certificate:" >>$OW_CERT_LOG
ls $OW_ROOT_CA >>$OW_CERT_LOG
echo "Using pssphrase: [$(cat $OW_SPACE_BASE/input/passphrase.txt)]"

export OW_SELFSIGN_CERT=$OW_SPACE_BASE/Certificates/BBRootCA.crt
openssl req -config $OW_SPACE_BASE/openssl.conf -new -x509 -days 3650 -key $OW_ROOT_CA -passin file:$OW_SPACE_BASE/input/passphrase.txt -out $OW_SELFSIGN_CERT <$OW_CERT_IN
echo "Self-Signed Cerificate:" >>$OW_CERT_LOG
ls $OW_SELFSIGN_CERT >>$OW_CERT_LOG

# Export Root Certificate to Keystore
export OW_ROOT_KEYSTORE=$OW_SPACE_BASE/BBRootCA.keystore

keytool -genkey -alias server -keyalg RSA -keystore $OW_ROOT_KEYSTORE -keysize 2048 -storepass file:$OW_SPACE_BASE/input/passphrase.txt <$OW_STORE_IN
echo "Create Root Keystore:" >>$OW_CERT_LOG
ls $OW_ROOT_KEYSTORE >>$OW_CERT_LOG

echo "Export Self-Signed Cert to Root Keystore" >>$OW_CERT_LOG
keytool -export -alias server -keystore $OW_ROOT_KEYSTORE -rfc -file $OW_SELFSIGN_CERT -keypass file:$OW_SPACE_BASE/input/passphrase.txt -storepass file:$OW_SPACE_BASE/input/passphrase.txt

export OW_ROOT_TRUST=$OW_SPACE_BASE/BBRootCA.truststore
echo "Export to TrustStore" >>$OW_CERT_LOG
keytool -import -file $OW_SELFSIGN_CERT -keystore $OW_ROOT_TRUST -keypass file:$OW_SPACE_BASE/input/passphrase.txt -storepass file:$OW_SPACE_BASE/input/passphrase.txt <$OW_TRUST_IN

echo "Creating Server Private Key"
export OW_SERVER_PRI_KEY=$OW_SPACE_BASE/Keys/BBServer.key
openssl genrsa -des3 -out $OW_SERVER_PRI_KEY -passout file:$OW_SPACE_BASE/input/passphrase.txt 2048

echo " "
echo "Creating Server CSR"
export OW_SERVER_CSR=$OW_SPACE_BASE/CSR/BBServer.csr
openssl req -config $OW_SPACE_BASE/openssl.conf -new -key $OW_SERVER_PRI_KEY -out $OW_SERVER_CSR -passin file:$OW_SPACE_BASE/input/passphrase.txt <$OW_CSR_IN

echo " "
echo "Creating Server Cert"
export OW_SERVER_CERT=$OW_SPACE_BASE/Certificates/BBServer.crt
openssl ca -verbose  -config $OW_SPACE_BASE/openssl.conf -days 3650 -in $OW_SERVER_CSR -out $OW_SERVER_CERT -keyfile $OW_ROOT_CA -key $OW_SPACE_BASE/input/passphrase.txt -cert $OW_SELFSIGN_CERT



echo "-----------------------------" >>$OW_CERT_LOG
echo "Summary:"
echo "-----------------------------" >>$OW_CERT_LOG
echo "Root Certificate: $OW_ROOT_CA "
echo "Root Self-Signed Certificate: $OW_SELFSIGN_CERT "
echo "Root Keystore: $OW_ROOT_KEYSTORE"
echo "Root Truststore: $OW_ROOT_TRUST "
echo "Server Private Key: $OW_SERVER_PRI_KEY "
echo "Server CSR: $OW_SERVER_CSR "
echo "Server Certificate: $OW_SERVER_CERT"
echo "-----------------------------" >>$OW_CERT_LOG
# cat $OW_CERT_LOG
echo "Done." >>$OW_CERT_LOG
echo "Done..."
