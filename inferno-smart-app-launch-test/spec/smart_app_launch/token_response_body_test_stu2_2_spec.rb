require_relative '../../lib/smart_app_launch/token_exchange_test'

RSpec.describe SMARTAppLaunch::TokenResponseBodyTestSTU22, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_response_body_stu2_2') }
  let(:valid_body) do
    {
      access_token: 'ACCESS_TOKEN',
      token_type: 'bearer',
      expires_in: 3600,
      scope: 'patient/*.*'
    }
  end
  let(:suite_id) { 'smart_stu2_2'}
  let(:runnable_inputs) do
    { smart_auth_info: Inferno::DSL::AuthInfo.new(requested_scopes: 'patient/*.*') }
  end

  def create_token_request(body: nil, status: 200, headers: nil)
    headers ||= [
      {
        type: 'response',
        name: 'Cache-Control',
        value: 'no-store'
      },
      {
        type: 'response',
        name: 'Pragma',
        value: 'no-cache'
      }
    ]
    repo_create(
      :request,
      direction: 'outgoing',
      name: 'token',
      url: 'http://example.com/token',
      test_session_id: test_session.id,
      response_body: body.is_a?(Hash) ? body.to_json : body,
      status:,
      headers:
    )
  end

  it 'passes if the body contains the required fields' do
    create_token_request(body: valid_body)

    result = run(test, runnable_inputs)

    expect(result.result).to eq('pass')
  end

  it 'skips if the token request was not successful' do
    create_token_request(body: { access_token: 'ACCESS_TOKEN', token_type: 'bearer' }, status: 500)

    result = run(test, runnable_inputs)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/was unsuccessful/)
  end

  it 'fails if the body is not valid json' do
    create_token_request(body: '[[')

    result = run(test, runnable_inputs)
    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JSON/)
  end

  it 'fails if the body does not contain a required field' do
    valid_body.each_key do |field|
      bad_body = valid_body.reject { |key, _| key == field }
      create_token_request(body: bad_body)

      result = run(test, runnable_inputs)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/`#{field}`/)
    end
  end

  it 'fails is the fields are the wrong types' do
    described_class::STRING_FIELDS.each do |field|
      body = valid_body.merge(field => 123)
      create_token_request(body:)

      result = run(test, runnable_inputs)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/String/)
    end

    described_class::NUMERIC_FIELDS.each do |field|
      body = valid_body.merge(field => '123')
      create_token_request(body:)

      result = run(test, runnable_inputs)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/Numeric/)
    end
  end

  context 'when the fhirContext field is present' do
    it 'passes if fhirContext valid' do
      canonicalURL = 'https://example.org/Organization/123/|v2023-05-03'
      canonicalURL2 = 'https://example.org/Organization/456|v2023-05-03'
      canonicalURL3 = 'https://example.org/Organization/890&version=0.8'
      identifierObj = {
        'system' => 'http://www.acme.org.au/units',
        'value' => 'ClinLab'
      }
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123' }, { reference: 'DiagnosticReport/123' },
                                            { reference: 'Observation/123/_history/2' }, { canonical: canonicalURL },
                                            { canonical: canonicalURL2 }, { canonical: canonicalURL3 },
                                            { identifier: identifierObj, type: 'Organization' }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('pass')
    end

    it 'fails if fhirContext is not an Array' do
      body = valid_body.merge(fhirContext: 'Organization/123')
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`fhirContext` field is a String, but should be an Array')
    end

    it 'fails if fhirContext contains a non-Hash element' do
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123' }, 'Organization/123'])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`\"Organization/123\"` is not an Object')
    end

    it 'fails if fhirContext does not include a reference, canonical, or identifier field' do
      body = valid_body.merge(fhirContext: [{ resource: 'Organization/123' }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match(
        '`fhirContext` array SHALL include at least one of "reference", "canonical", or "identifier"'
      )
    end

    it 'fails if fhirContext reference contains a non-String element' do
      numericalElement = 123
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123' }, { reference: numericalElement }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{numericalElement}` is not a String")
    end

    it 'fails if fhirContext contains a reference that is not a relative reference' do
      canonicalURL = 'https://example.org/Organization/123/|v2023-05-03'
      body = valid_body.merge(fhirContext: [{ reference: canonicalURL }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{canonicalURL}` is not a relative reference")
    end

    it 'fails if fhirContext contains a reference with an invalid resource type' do
      invalidResourceType = 'Hospital'
      body = valid_body.merge(fhirContext: [{ reference: "#{invalidResourceType}/123" }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match(
        "`#{invalidResourceType}` in `reference` is not a valid FHIR resource type"
      )
    end

    it 'fails if fhirContext contains a reference with an invalid id' do
      invalidFhirID = '@#'
      body = valid_body.merge(fhirContext: [{ reference: "Organization/#{invalidFhirID}" }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{invalidFhirID}` in `reference` is not a valid FHIR id")
    end

    it 'fails if fhirContext canonical contains a non-String element' do
      numericalElement = 123
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123' }, { canonical: numericalElement }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{numericalElement}` is not a String")
    end

    it 'fails if fhirContext contains a canonical that is not an absolute reference' do
      body = valid_body.merge(fhirContext: [{ canonical: 'Organization/123' }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`Organization/123` is not a canonical reference')
    end

    it 'fails if fhirContext contains a canonical with an invalid resource type' do
      canonicalURL = 'https://example.org/Hospital/123/|v2023-05-03'
      body = valid_body.merge(fhirContext: [{ canonical: canonicalURL }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`Hospital` in `canonical` is not a valid FHIR resource type')
    end

    it 'fails if fhirContext contains a canonical with an invalid id' do
      invalidFhirID = '@#'
      canonicalURL = "https://example.org/Organization/#{invalidFhirID}/|v2023-05-03"
      body = valid_body.merge(fhirContext: [{ canonical: canonicalURL }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{invalidFhirID}` in `canonical` is not a valid FHIR id")
    end

    it 'fails if fhirContext identifier contains a non-Hash element' do
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123' }, { identifier: 'Organization/123' }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`"Organization/123"` is not an Object')
    end

    it 'fails if fhirContext type contains an invalid resource type' do
      body = valid_body.merge(fhirContext: [{ reference: 'Organization/123', type: 'Hospital' }])
      create_token_request(body:)

      result = run(test, runnable_inputs)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`Hospital` in `type` is not a valid FHIR resource type')
    end
  end

  it 'persists outputs' do
    inputs = {
      access_token: 'ACCESS_TOKEN',
      id_token: 'ID_TOKEN',
      refresh_token: 'REFRESH_TOKEN',
      expires_in: 3600,
      patient: 'PATIENT',
      encounter: 'ENCOUNTER',
      scope: 'SCOPE',
      token_type: 'BEARER',
      intent: 'INTENT'
    }
    expected_outputs = {
      id_token: inputs[:id_token],
      refresh_token: inputs[:refresh_token],
      access_token: inputs[:access_token],
      expires_in: inputs[:expires_in],
      patient_id: inputs[:patient],
      encounter_id: inputs[:encounter],
      received_scopes: inputs[:scope],
      intent: inputs[:intent]
    }
    create_token_request(body: inputs)

    runnable_inputs[:smart_auth_info].requested_scopes = 'SCOPE'
    result = run(test, runnable_inputs)

    expect(result.result).to eq('pass')

    expected_outputs.each do |name, value|
      persisted_data = session_data_repo.load(test_session_id: test_session.id, name:)

      expect(persisted_data).to eq(value.to_s)
    end

    persisted_auth_info = JSON.parse(session_data_repo.load(test_session_id: test_session.id, name: :smart_auth_info))

    expect(persisted_auth_info['refresh_token']).to eq(inputs[:refresh_token])
    expect(persisted_auth_info['access_token']).to eq(inputs[:access_token])
    expect(persisted_auth_info['expires_in']).to eq(inputs[:expires_in])
  end
end
