# flake8: noqa
from django.conf import settings


"""
    mock_fhir_responses: A dictionary of short FHIR service mock responses
                         to be used for APIClient tests that call the
                         back end FHIR service.

    Contains successful responses for Patient, EOB, and Coverage end points
    for the settings.DEFAULT_SAMPLE_FHIR_ID

    See apps.dot_ext.tests.test_views.TestAuthorizationView() for example usage.
"""
mock_fhir_responses = {
    "success_patient_searchview": {
        "status_code": 200,
        "content": {
            "resourceType": "Bundle",
            "id": "09377c85-f54f-49ff-b23c-270ce0074b7b",
            "meta": {
              "lastUpdated": "2020-07-07T20:40:21.347+00:00"
            },
            "type": "searchset",
            "total": 1,
            "link": [
              {
                "relation": "first",
                "url": "http://localhost:8000/v1/fhir/Patient?_format=application%2Fjson%2Bfhir&startIndex=0&_count=10&_id=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "last",
                "url": "http://localhost:8000/v1/fhir/Patient?_format=application%2Fjson%2Bfhir&startIndex=0&_count=10&_id=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "self",
                "url": "http://localhost:8000/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=" + settings.DEFAULT_SAMPLE_FHIR_ID + "&startIndex=0"
              }
            ],
            "entry": [
              {
                "resource": {
                  "resourceType": "Patient",
                  "id": settings.DEFAULT_SAMPLE_FHIR_ID,
                  "meta": {
                    "lastUpdated": "2020-07-07T20:40:20.685+00:00"
                  },
                  "extension": [
                    {
                      "url": "https://bluebutton.cms.gov/resources/variables/race",
                      "valueCoding": {
                        "system": "https://bluebutton.cms.gov/resources/variables/race",
                        "code": "1",
                        "display": "White"
                      }
                    },
                  ],
                  "identifier": [
                    {
                      "system": "https://bluebutton.cms.gov/resources/variables/bene_id",
                      "value": settings.DEFAULT_SAMPLE_FHIR_ID
                    },
                    {
                      "system": "https://bluebutton.cms.gov/resources/identifier/mbi-hash",
                      "value": "abadf57ff8dc94610ca0d479feadb1743c9cd3c77caf1eafde5719a154379fb6"
                    }
                  ],
                  "name": [
                    {
                      "use": "usual",
                      "family": "Doe",
                      "given": [
                        "Jane",
                        "X"
                      ]
                    }
                  ],
                  "gender": "female",
                  "birthDate": "2014-06-01",
                  "address": [
                    {
                      "district": "999",
                      "state": "15",
                      "postalCode": "99999"
                    }
                  ]
                }
              }
            ]
        },
    },
    "success_patient_readview": {
        "status_code": 200,
        "content": {
            "resourceType": "Patient",
            "id": "-20140000008325",
            "meta": {
              "lastUpdated": "2020-07-07T20:40:20.685+00:00"
            },
            "identifier": [
              {
                "system": "https://bluebutton.cms.gov/resources/variables/bene_id",
                "value": "-20140000008325"
              },
              {
                "system": "https://bluebutton.cms.gov/resources/identifier/mbi-hash",
                "value": "abadf57ff8dc94610ca0d479feadb1743c9cd3c77caf1eafde5719a154379fb6"
              }
            ],
            "name": [
              {
                "use": "usual",
                "family": "Doe",
                "given": [
                  "Jane",
                  "X"
                ]
              }
            ],
            "gender": "female",
            "birthDate": "2014-06-01",
            "address": [
              {
                "district": "999",
                "state": "15",
                "postalCode": "99999"
              }
            ]
          }
    },
    "success_eob": {
        "status_code": 200,
        "content": {
            "resourceType": "Bundle",
            "id": "09377c85-f54f-49ff-b23c-270ce0074b7b",
            "meta": {
              "lastUpdated": "2020-07-07T20:40:21.347+00:00"
            },
            "type": "searchset",
            "total": 0,
            "link": [
              {
                "relation": "first",
                "url": "http://localhost:8000/v1/fhir/ExplanationOfBenefit?_format=application%2Fjson%2Bfhir&startIndex=0&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "next",
                "url": "http://localhost:8000/v1/fhir/ExplanationOfBenefit?_format=application%2Fjson%2Bfhir&startIndex=10&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "last",
                "url": "http://localhost:8000/v1/fhir/ExplanationOfBenefit?_format=application%2Fjson%2Bfhir&startIndex=30&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "self",
                "url": "http://localhost:8000/v1/fhir/ExplanationOfBenefit/?_count=10&_format=application%2Fjson%2Bfhir&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID + "&startIndex=0"
              }
            ],
            "entry": [
              {
                "resource": {
                  "resourceType": "ExplanationOfBenefit",
                  "id": "carrier--20587716665",
                  "meta": {
                    "lastUpdated": "2020-01-01T00:00:00.000+00:00"
                  },
              }
            }
            ]
        },
    },
    "success_coverage": {
        "status_code": 200,
        "content": {
            "resourceType": "Bundle",
            "id": "09377c85-f54f-49ff-b23c-270ce0074b7b",
            "meta": {
              "lastUpdated": "2020-07-07T20:40:21.347+00:00"
            },
            "type": "searchset",
            "total": 0,
            "link": [
              {
                "relation": "first",
                "url": "http://localhost:8000/v1/fhir/Coverage?_format=application%2Fjson%2Bfhir&startIndex=0&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "next",
                "url": "http://localhost:8000/v1/fhir/Coverage?_format=application%2Fjson%2Bfhir&startIndex=10&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "last",
                "url": "http://localhost:8000/v1/fhir/Coverage?_format=application%2Fjson%2Bfhir&startIndex=30&_count=10&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID
              },
              {
                "relation": "self",
                "url": "http://localhost:8000/v1/fhir/Coverage/?_count=10&_format=application%2Fjson%2Bfhir&patient=" + settings.DEFAULT_SAMPLE_FHIR_ID + "&startIndex=0"
              }
            ],
            "entry": [
              {
                "resource": {
                  "resourceType": "Coverage",
                  "id": "carrier--20587716665",
                  "meta": {
                    "lastUpdated": "2020-01-01T00:00:00.000+00:00"
                  },
              }
            }
            ]
        },
    },
}
