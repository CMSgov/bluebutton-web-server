require_relative '../../lib/smart_app_launch/openid_fhir_user_claim_test'

RSpec.describe SMARTAppLaunch::OpenIDFHIRUserClaimTest do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_openid_fhir_user_claim') }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }
  let(:scopes) { 'fhirUser' }
  let(:client_id) { 'CLIENT_ID' }
  let(:payload) do
    {
      fhirUser: "#{url}/Patient/123"
    }
  end
  let(:smart_auth_info) { Inferno::DSL::AuthInfo.new(requested_scopes: scopes) }
  let(:inputs) do
    {
      id_token_payload_json: payload.to_json,
      url: url,
      smart_auth_info:
    }
  end

  it 'skips if no token payload is available' do
    result = run(test, id_token_payload_json: nil, url: url, smart_auth_info:)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/Input 'id_token_payload_json' is nil/)
  end

  it 'skips if no fhirUser scope was requested' do
    inputs[:smart_auth_info].requested_scopes = 'launch'
    result = run(test, inputs)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/`fhirUser` scope not requested/)
  end

  it 'passes when the fhirUser claim is present and the user can be retrieved' do
    user_request =
      stub_request(:get, payload[:fhirUser])
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json)

    result = run(test, inputs)
    expect(result.result).to eq('pass')
    expect(user_request).to have_been_made
  end

  it 'fails if the fhirUser claim is blank' do
    inputs[:id_token_payload_json] = { fhirUser: '' }.to_json
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/does not contain/)
  end

  it 'fails if the fhirUser claim does not refer to a valid resource type' do
    inputs[:id_token_payload_json] = { fhirUser: "#{url}/Observation/123" }.to_json
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/resource type/)
  end

  it 'fails if the incorrect resource type is returned' do
    user_request =
      stub_request(:get, payload[:fhirUser])
      .to_return(status: 200, body: FHIR::Person.new(id: '123').to_json)

    inputs[:id_token_payload_json] = { fhirUser: "#{url}/Patient/123" }.to_json
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Patient/)
    expect(user_request).to have_been_made
  end

  it 'fails when the fhirUser can not be retrieved' do
    user_request =
      stub_request(:get, payload[:fhirUser])
      .to_return(status: 404)
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to include('200')
    expect(user_request).to have_been_made
  end

  it 'persists outputs' do
    stub_request(:get, payload[:fhirUser])
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json)
    result = run(test, inputs)

    expect(result.result).to eq('pass')

    persisted_user = session_data_repo.load(test_session_id: test_session.id, name: :id_token_fhir_user)
    expect(persisted_user).to eq(payload[:fhirUser])
  end
end
