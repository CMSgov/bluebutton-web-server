patient_response = {
    "resourceType": "Bundle",
    "id": "d0c10556-a3df-4af6-bdb3-d60908b1f16b",
    "meta": {
        "lastUpdated": "2018-04-05T15:44:17.721-04:00"
    },
    "type": "searchset",
    "total": 1,
    "entry": [{
        "fullUrl": "https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/20140000008325",
        "resource": {
            "resourceType": "Patient",
            "id": "20140000008325",
            "extension": [{
                "url": "https://bluebutton.cms.gov/resources/variables/race",
                "valueCoding": {
                    "system": "https://bluebutton.cms.gov/resources/variables/race",
                    "code": "1",
                    "display": "White"
                }
            }],
            "identifier": [{
                "system": "https://bluebutton.cms.gov/resources/variables/bene_id",
                "value": "20140000008325"
            }, {
                "system": "https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                "value": "96228a57f37efea543f4f370f96f1dbf01c3e3129041dba3ea4367545507c6e7"
            }],
            "name": [{
                "use": "usual",
                "family": "Doe",
                "given": [
                    "Jane",
                    "X"
                ]
            }],
            "gender": "unknown",
            "birthDate": "1999-06-01",
            "address": [{
                "district": "999",
                "state": "30",
                "postalCode": "99999"
            }]
        }
    }]
}
