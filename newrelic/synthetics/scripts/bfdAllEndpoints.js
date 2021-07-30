/**
 * Feel free to explore, or check out the full documentation
 * https://docs.newrelic.com/docs/synthetics/new-relic-synthetics/scripting-monitors/writing-api-tests
 * for details.
 */

const assert = require("assert");
const BASE_URL = 'https://sandbox.bluebutton.cms.gov/';
const VERSIONS = ['v1', 'v2'];
const AUTH_TOKEN = $secure['Adjust Per Env'];

const generatePatientUrl = (version) => {
    return BASE_URL + version + '/fhir/Patient';
}

const generateCoverageUrl = (version) => {
    return BASE_URL + version + '/fhir/Coverage';
}

const generateEobUrl = (version) => {
    return BASE_URL + version + '/fhir/ExplanationOfBenefit';
}

const patientSuccessEvaluation = (url, parsedBody) => {
    assert.ok(parsedBody.total > 0, url + ': Expected the total number of patients to be greater than zero but received: ' + parsedBody.total);
}

const coverageSuccessEvaluation = (url, parsedBody) => {
    assert.ok(parsedBody.total > 0, url + ': Expected the total number of coverages to be greater than zero but received: ' + parsedBody.total);
}

const eobSuccessEvaluation = (url, parsedBody) => {
    assert.ok(parsedBody.total > 0, url + ': Expected the total number of EOBs to be greater than zero but received: ' + parsedBody.total);
}

const URL_EVALUATIONS = [
    {
        urlGenerator: generatePatientUrl,
        evaluate: patientSuccessEvaluation
    },
    {
        urlGenerator: generateCoverageUrl,
        evaluate: coverageSuccessEvaluation
    },
    {
        urlGenerator: generateEobUrl,
        evaluate: eobSuccessEvaluation
    }
];

for (const urlEvaluation of URL_EVALUATIONS) {
    for (const version of VERSIONS) {
        const requestOptions = {
            url: urlEvaluation.urlGenerator(version),
            headers: {
                'Authorization': 'Bearer ' + AUTH_TOKEN,
                'Content-Type': 'application/json'
            }
        }

        $http.get(requestOptions, function (err, response, body) {
            if (err) {
                console.log(err);
            }
            assert.ok(
                response.statusCode === 200,
                requestOptions.url + ': Expected response status code to be 200, instead received: ' + response.statusCode
            );
            const parsedBody = JSON.parse(body);
            urlEvaluation.evaluate(requestOptions.url, parsedBody);
        });
    }
}