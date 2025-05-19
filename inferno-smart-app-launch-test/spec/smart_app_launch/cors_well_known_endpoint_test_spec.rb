require_relative '../../lib/smart_app_launch/cors_well_known_endpoint_test'

RSpec.describe SMARTAppLaunch::CORSWellKnownEndpointTest do
  let(:suite_id) { 'smart_stu2_2' }
  let(:test) { Inferno::Repositories::Tests.new.find('smart_cors_well_known_endpoint') }
  let(:url) { 'http://example.com/fhir' }
  let(:well_known_url) { 'http://example.com/fhir/.well-known/smart-configuration' }
  let(:well_known_config) do
    {
      'authorization_endpoint' => 'https://example.com/fhir/auth/authorize',
      'token_endpoint' => 'https://example.com/fhir/auth/token',
      'token_endpoint_auth_methods_supported' => ['client_secret_basic'],
      'registration_endpoint' => 'https://example.com/fhir/auth/register',
      'scopes_supported' =>
        ['openid', 'profile', 'launch', 'launch/patient', 'patient/*.*', 'user/*.*', 'offline_access'],
      'response_types_supported' => ['code', 'code id_token', 'id_token', 'refresh_token'],
      'management_endpoint' => 'https://example.com/fhir/user/manage',
      'introspection_endpoint' => 'https://example.com/fhir/user/introspect',
      'revocation_endpoint' => 'https://example.com/fhir/user/revoke',
      'capabilities' =>
        ['launch-ehr', 'client-public', 'client-confidential-symmetric', 'context-ehr-patient', 'sso-openid-connect'],
      'issuer' => 'https://example.com',
      'jwks_uri' => 'https://example.com/.well-known/jwks.json',
      'grant_types_supported' => ['authorization_code'],
      'code_challenge_methods_supported' => ['S256']
    }
  end

  def cors_header(value)
    {
      'Access-Control-Allow-Origin' => value
    }
  end

  it 'passes when well_known request is returned with valid origin cors header' do
    well_known_request = stub_request(:get, well_known_url)
      .to_return(status: 200, body: well_known_config.to_json,
                 headers: { 'Content-Type' => 'application/json',
                            'Access-Control-Allow-Origin' => Inferno::Application['inferno_host'] })
    result = run(test, url:)
    expect(result.result).to eq('pass')
    expect(well_known_request).to have_been_made
  end

  it 'passes when well_known request is returned with valid wildcard cors header' do
    well_known_request = stub_request(:get, well_known_url)
      .to_return(status: 200, body: well_known_config.to_json,
                 headers: { 'Content-Type' => 'application/json',
                            'Access-Control-Allow-Origin' => '*' })
    result = run(test, url:)

    expect(result.result).to eq('pass')
    expect(well_known_request).to have_been_made
  end

  it 'fails when a non-200 response is received' do
    well_known_request = stub_request(:get, well_known_url)
      .to_return(status: 500, body: well_known_config.to_json,
                 headers: { 'Content-Type' => 'application/json',
                            'Access-Control-Allow-Origin' => Inferno::Application['inferno_host'] })

    result = run(test, url:)

    expect(result.result).to eq('fail')
    expect(well_known_request).to have_been_made
    expect(result.result_message).to match(/Unexpected response status/)
  end

  it 'fails when a response with no cors header is received' do
    well_known_request = stub_request(:get, well_known_url)
      .to_return(status: 200, body: well_known_config.to_json,
                 headers: { 'Content-Type' => 'application/json' })

    result = run(test, url:)

    expect(result.result).to eq('fail')
    expect(well_known_request).to have_been_made
    expect(result.result_message).to match('No `Access-Control-Allow-Origin` header received')
  end

  it 'fails when a response with incorrect cors header is received' do
    well_known_request = stub_request(:get, well_known_url)
      .to_return(status: 200, body: well_known_config.to_json,
                 headers: { 'Content-Type' => 'application/json',
                            'Access-Control-Allow-Origin' => 'https://incorrect-origin.com' })

    result = run(test, url:)

    expect(result.result).to eq('fail')
    expect(well_known_request).to have_been_made
    expect(result.result_message).to match(/`Access-Control-Allow-Origin` must be/)
  end
end
