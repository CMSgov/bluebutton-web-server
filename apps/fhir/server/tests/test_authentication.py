from django.test import TestCase
from django.conf import settings
from rest_framework import exceptions
from requests.exceptions import HTTPError
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from httmock import all_requests, HTTMock
from ..models import ResourceRouter
from ..authentication import match_hicn_hash


responses = {
    "success": {
        "status_code": 200,
        "content": {
            "resourceType":"Bundle",
            "id":"389a548b-9c85-4491-9795-9306a957030b",
            "meta":{
                "lastUpdated":"2019-12-18T13:40:02.792-05:00"
            },
            "type":"searchset",
            "total":1,
            "link":[
                {
                    "relation":"first",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"last",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"self",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=-20000000002346&startIndex=0"
                }
            ],
            "entry":[
                {
                    "resource":{
                        "resourceType":"Patient",
                        "id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }
            ]
        },
    },
    "not_found": {
        "status_code": 200,
        "content": {
            "resourceType":"Bundle",
            "id":"389a548b-9c85-4491-9795-9306a957030b",
            "meta":{
                "lastUpdated":"2019-12-18T13:40:02.792-05:00"
            },
            "type":"searchset",
            "total":0,
            "link":[
                {
                    "relation":"first",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"last",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"self",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=-20000000002346&startIndex=0"
                }
            ],
            "entry":[],
        },
    },
    "error": {
        "status_code": 500,
    },
    "duplicates": {
        "status_code": 200,
        "content": {
            "resourceType":"Bundle",
            "id":"389a548b-9c85-4491-9795-9306a957030b",
            "meta":{
                "lastUpdated":"2019-12-18T13:40:02.792-05:00"
            },
            "type":"searchset",
            "total":2,
            "link":[
                {
                    "relation":"first",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"last",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"self",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=-20000000002346&startIndex=0"
                }
            ],
            "entry":[
                {
                    "resource":{
                        "resourceType":"Patient",
                        "id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }, {
                    "resource":{
                        "resourceType":"Patient",
                        "id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }
            ]
        },
    },
    "malformed": {
        "status_code": 200,
        "content": {
            "resourceType":"Bundle",
            "id":"389a548b-9c85-4491-9795-9306a957030b",
            "meta":{
                "lastUpdated":"2019-12-18T13:40:02.792-05:00"
            },
            "type":"searchset",
            "total":1,
            "link":[
                {
                    "relation":"first",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"last",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"self",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=-20000000002346&startIndex=0"
                }
            ],
            "entry":[
                {
                    "resource":{
                        "resourceType":"Patient",
                        "_id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }
            ]
        },
    },
    "lying": {
        "status_code": 200,
        "content": {
            "resourceType":"Bundle",
            "id":"389a548b-9c85-4491-9795-9306a957030b",
            "meta":{
                "lastUpdated":"2019-12-18T13:40:02.792-05:00"
            },
            "type":"searchset",
            "total":1,
            "link":[
                {
                    "relation":"first",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"last",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_count=10&startIndex=0&_id=-20000000002346"
                },
                {
                    "relation":"self",
                    "url":"https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/?_count=10&_format=application%2Fjson%2Bfhir&_id=-20000000002346&startIndex=0"
                }
            ],
            "entry":[
                {
                    "resource":{
                        "resourceType":"Patient",
                        "id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }, {
                    "resource":{
                        "resourceType":"Patient",
                        "id":"-20000000002346",
                        "extension":[
                            {
                                "url":"https://bluebutton.cms.gov/resources/variables/race",
                                "valueCoding":{
                                    "system":"https://bluebutton.cms.gov/resources/variables/race",
                                    "code":"1",
                                    "display":"White"
                                }
                            }
                        ],
                        "identifier":[
                            {
                                "system":"https://bluebutton.cms.gov/resources/variables/bene_id",
                                "value":"-20000000002346"
                            },
                            {
                                "system":"https://bluebutton.cms.gov/resources/identifier/hicn-hash",
                                "value":"50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b"
                            }
                        ],
                        "name":[
                            {
                                "use":"usual",
                                "family":"Doe",
                                "given":[
                                    "John",
                                    "X"
                                ]
                            }
                        ],
                        "gender":"male",
                        "birthDate":"2000-06-01",
                        "address":[
                            {
                                "district":"999",
                                "state":"48",
                                "postalCode":"99999"
                            }
                        ]
                    }
                }
            ]
        },
    },
}





class TestAuthentication(TestCase):

    def setUp(self):
        ResourceRouter.objects.create(pk=settings.FHIR_SERVER_DEFAULT,
                                      fhir_url="http://bogus.com/")

    def test_match_hicn_hash_success(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['success']
        with HTTMock(fhir_mock):
            fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")
            self.assertEqual(backend_data, responses['success']['content'])
            self.assertEqual(fhir_id, "-20000000002346")
        
    def test_match_hicn_hash_not_found(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['not_found']
        with HTTMock(fhir_mock):
            with self.assertRaises(exceptions.NotFound):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_server_error(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['error']
        with HTTMock(fhir_mock):
            with self.assertRaises(HTTPError):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_duplicates(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['duplicates']
        with HTTMock(fhir_mock):
            with self.assertRaises(UpstreamServerException):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_malformed(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['malformed']
        with HTTMock(fhir_mock):
            with self.assertRaises(KeyError):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")

    def test_match_hicn_hash_lying_duplicates(self):
        @all_requests
        def fhir_mock(url, request):
            return responses['lying']
        with HTTMock(fhir_mock):
            with self.assertRaises(UpstreamServerException):
                fhir_id, backend_data = match_hicn_hash("50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b")
