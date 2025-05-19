require_relative '../../lib/smart_app_launch/cors_openid_fhir_user_claim_test'

RSpec.describe SMARTAppLaunch::CORSOpenIDFHIRUserClaimTest do
  let(:suite_id) { 'smart_stu2_2' }
  let(:test) { Inferno::Repositories::Tests.new.find('smart_cors_openid_fhir_user_claim') }

  let(:client_id) { 'CLIENT_ID' }
  let(:smart_auth_info) do
    {
      auth_type: 'public',
      access_token: 'ACCESS_TOKEN',
      refresh_token: 'REFRESH_TOKEN',
      expires_in: 3600,
      client_id:,
      issue_time: Time.now.iso8601,
      token_url: 'http://example.com/token'
    }.to_json
  end
  let(:url) { 'http://example.com/fhir' }
  let(:id_token_fhir_user) { "#{url}/Patient/123" }

  def cors_header(value)
    {
      'Access-Control-Allow-Origin' => value
    }
  end

  it 'passes when the fhir user can be retrieved with valid origin cors header' do
    user_request =
      stub_request(:get, id_token_fhir_user)
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json,
                 headers: cors_header(Inferno::Application['inferno_host']))

    result = run(
      test,
      url:,
      smart_auth_info:,
      id_token_fhir_user:
    )

    expect(result.result).to eq('pass')
    expect(user_request).to have_been_made
  end

  it 'passes when the fhir user can be retrieved with valid wildcard cors header' do
    user_request =
      stub_request(:get, id_token_fhir_user)
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json,
                 headers: cors_header('*'))
    result = run(
      test,
      url:,
      smart_auth_info:,
      id_token_fhir_user:
    )

    expect(result.result).to eq('pass')
    expect(user_request).to have_been_made
  end

  it 'fails when a non-200 response is received' do
    user_request =
      stub_request(:get, id_token_fhir_user)
      .to_return(status: 500, body: FHIR::Patient.new(id: '123').to_json,
                 headers: cors_header(Inferno::Application['inferno_host']))

    result = run(
      test,
      url:,
      smart_auth_info:,
      id_token_fhir_user:
    )

    expect(result.result).to eq('fail')
    expect(user_request).to have_been_made
    expect(result.result_message).to match(/Unexpected response status/)
  end

  it 'fails when a response with no cors header is received' do
    user_request =
      stub_request(:get, id_token_fhir_user)
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json)

    result = run(
      test,
      url:,
      smart_auth_info:,
      id_token_fhir_user:
    )

    expect(result.result).to eq('fail')
    expect(user_request).to have_been_made
    expect(result.result_message).to match('No `Access-Control-Allow-Origin` header received')
  end

  it 'fails when a response with incorrect cors header is received' do
    user_request =
      stub_request(:get, id_token_fhir_user)
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json,
                 headers: cors_header('https://incorrect-origin.com'))

    result = run(
      test,
      url:,
      smart_auth_info:,
      id_token_fhir_user:
    )

    expect(result.result).to eq('fail')
    expect(user_request).to have_been_made
    expect(result.result_message).to match(/`Access-Control-Allow-Origin` must be/)
  end
end
