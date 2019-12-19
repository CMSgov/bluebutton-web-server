patient_response = {
    "total": 1,
    "resourceType": "Bundle",
    "type": "searchset",
    "link": [
        {
            "url": "http://localhost:8000/v1/fhir/Patient?_count=5&startIndex=0&_id=-20140000008325",
            "relation": "first"
        },
        {
            "url": "http://localhost:8000/v1/fhir/Patient?_count=5&startIndex=0&_id=-20140000008325",
            "relation": "last"
        },
        {
            "url": "http://localhost:8000/v1/fhir/Patient/?_count=5&_format=application%2Fjson%2Bfhir&_id=-20140000008325&startIndex=0",  # noqa
            "relation": "self"
        }
    ],
    "id": "4250e2c5-8956-40a1-9809-1be08ba542f7",
    "entry": [
        {
            "resource": {
                "name": [
                    {
                        "given": [
                            "Jane",
                            "X"
                        ],
                        "family": "Doe",
                        "use": "usual"
                    }
                ],
                "extension": [
                    {
                        "valueCoding": {
                            "system": "https://bluebutton.cms.gov/resources/variables/race",
                            "display": "White",
                            "code": "1"
                        },
                        "url": "https://bluebutton.cms.gov/resources/variables/race"
                    }
                ],
                "identifier": [
                    {
                        "value": "-20140000008325",
                        "system": "https://bluebutton.cms.gov/resources/variables/bene_id"
                    },
                    {
                        "value": "2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5",
                        "system": "https://bluebutton.cms.gov/resources/identifier/hicn-hash"
                    }
                ],
                "resourceType": "Patient",
                "id": "-20140000008325",
                "address": [
                    {
                        "state": "15",
                        "district": "999",
                        "postalCode": "99999"
                    }
                ],
                "gender": "female",
                "birthDate": "2014-06-01"
            }
        }
    ],
    "meta": {
        "lastUpdated": "2019-06-27T08:17:11.811-04:00"
    }
}
