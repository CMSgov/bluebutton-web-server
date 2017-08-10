# Secure Exchange of Sensitive Values

## Background

The Blue Button project needed a capability to match beneficiaries to their 
data from the Chronic Condition Warehouse.

The requirements were:
- A unique value for each beneficiary
- A value that the beneficiary, or a health care organization, would know
 
 
The obvious solution is to use the Social Security Number(SSN). THe challenge 
with using the SSN is that it is sensitive data that should not be committed 
to system logs, or transmitted in the clear.

The challenge was also to enable this value to be searched for in the back-end
system using the standard features of FHIR.

## Blue Button matching method

Our chosen approach is to encrypt the SSN with a one-way hash. 
The actual SSN is only required during account registration. Once the hash
has been generated the SSN is no longer required.

When a FHIR Patient record is created during the ETL process a hash of the 
SSN is generated. This is stored in the FHIR Patient Record as an Identifier.
 
When a beneficiary account is created the SSN is used to generate a hash 
value using the same hashing algorithm. The front-end OAuth server uses
the hash value to search the Patient records in the back-end HAPI Server 
looking for a match on identifier

```
[base]/Patient/?identifier={hash_value}

```

If the search returns a searchset of a single record there is a match.
the id of the matching Patienr resource can be saved to the Front-end 
Crosswalk table in the fhir_id field. 

## Notes

- This approach can be used with any sensitive values that can be used to link
patients with their records. 
- This approach is best used within a closed system environment. Managing the 
hashing algorithm and key values that seed the algorithm does not lend itself 
to large federated deployments.
 
 



