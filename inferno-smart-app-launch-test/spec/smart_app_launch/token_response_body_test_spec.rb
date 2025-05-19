require_relative '../../lib/smart_app_launch/token_exchange_test'

RSpec.describe SMARTAppLaunch::TokenResponseBodyTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_response_body') }
  let(:valid_body) do
    {
      access_token: 'ACCESS_TOKEN',
      token_type: 'bearer',
      expires_in: 3600,
      scope: 'patient/*.*'
    }
  end
  let(:suite_id) { 'smart'}
  let(:input) do
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
      status: status,
      headers: headers
    )
  end

  it 'passes if the body contains the required fields' do
    create_token_request(body: valid_body)

    result = run(test, input)

    expect(result.result).to eq('pass')
  end

  it 'skips if the token request was not successful' do
    create_token_request(body: { access_token: 'ACCESS_TOKEN', token_type: 'bearer' }, status: 500)

    result = run(test, input)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/was unsuccessful/)
  end

  it 'fails if the body is not valid json' do
    create_token_request(body: '[[')

    result = run(test, input)
    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JSON/)
  end

  it 'fails if the body does not contain a required field' do
    valid_body.each_key do |field|
      bad_body = valid_body.reject { |key, _| key == field }
      create_token_request(body: bad_body)

      result = run(test, input)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/`#{field}`/)
    end
  end

  it 'fails is the fields are the wrong types' do
    described_class::STRING_FIELDS.each do |field|
      body = valid_body.merge(field => 123)
      create_token_request(body: body)

      result = run(test, input)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/String/)
    end

    described_class::NUMERIC_FIELDS.each do |field|
      body = valid_body.merge(field => '123')
      create_token_request(body: body)

      result = run(test, input)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/Numeric/)
    end
  end

  context 'when the fhirContext field is present' do
    it 'passes if fhirContext valid' do
      body = valid_body.merge(fhirContext: ['Organization/123', 'DiagnosticReport/123', 'Observation/123/_history/2'])
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('pass')
    end

    it 'fails if fhirContext is not an Array' do
      body = valid_body.merge(fhirContext: 'Organization/123')
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match('`fhirContext` field is a String, but should be an Array')
    end

    it 'fails if fhirContext contains a non-string element' do
      numericalElement = 123
      body = valid_body.merge(fhirContext: ['Organization/123', numericalElement])
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{numericalElement}` is not a string")
    end

    it 'fails if fhirContext contains an absolute reference' do
      canonicalURL = 'https://example.org/Organization/123/|v2023-05-03'
      body = valid_body.merge(fhirContext: [canonicalURL])
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{canonicalURL}` is not a relative reference")
    end

    it 'fails if fhirContext contains a reference with an invalid resource type' do
      invalidResourceType = 'Hospital'
      body = valid_body.merge(fhirContext: ["#{invalidResourceType}/123"])
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{invalidResourceType}` is not a valid FHIR resource type")
    end

    it 'fails if fhirContext contains a reference with an invalid id' do
      invalidFhirID = '@#'
      body = valid_body.merge(fhirContext: ["Organization/#{invalidFhirID}"])
      create_token_request(body: body)

      result = run(test, input)
      expect(result.result).to eq('fail')
      expect(result.result_message).to match("`#{invalidFhirID}` is not a valid FHIR id")
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

    input[:smart_auth_info].requested_scopes = 'SCOPE'
    result = run(test, input)

    expect(result.result).to eq('pass')

    expected_outputs.each do |name, value|
      persisted_data = session_data_repo.load(test_session_id: test_session.id, name: name)

      expect(persisted_data).to eq(value.to_s)
    end
  end
end
