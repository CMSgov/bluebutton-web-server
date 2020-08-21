# Put BB2 server's cert & key for secured connection with BFD FHIR server

ca.cert.pem - certificate
ca.key.nocrypt.pem - private key

Ask for cert and key that works with the
targeted BFD FHIR server.

# Put target BFD server's certificate for SSL verify

ca_bundle.pem - server certificate - ca signed (for production) or self signed (for test or dev)
