require_relative '../../lib/smart_app_launch/backend_services_authorization_response_body_test'

RSpec.describe SMARTAppLaunch::BackendServicesAuthorizationResponseBodyTest do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_backend_services_auth_response_body') }
  let(:suite_id) { 'smart_stu2'}

  let(:response_body) do
    {
      'access_token' => 'this_is_the_token',
      'token_type' => 'its_a_token',
      'expires_in' => 'a_couple_minutes',
      'scope' => 'system'
    }
  end

  it 'skips when no authentication response received' do
    result = run(test)

    expect(result.result).to eq('skip')
    expect(result.result_message).to eq("Input 'authentication_response' is nil, skipping test.")
  end

  it 'fails when authentication response is invalid JSON' do
    result = run(test, { authentication_response: '{/}' })

    expect(result.result).to eq('fail')
    expect(result.result_message).to eq('Invalid JSON. ')
  end

  it 'fails when authentication response does not contain access_token' do
    result = run(test, { authentication_response: '{"response_body":"post"}' })

    expect(result.result).to eq('fail')
    expect(result.result_message).to eq('Token response did not contain access_token as required')
  end

  it 'fails when access_token is present but does not contain required keys' do
    missing_key_auth_response = { 'access_token' => 'its_the_token' }
    result = run(test, { authentication_response: missing_key_auth_response.to_json })

    expect(result.result).to eq('fail')
    expect(result.result_message).to eq('Token response did not contain token_type as required')
  end

  it 'passes when access_token is present and contains the required keys' do
    result = run(test, { authentication_response: response_body.to_json })

    expect(result.result).to eq('pass')
  end
end
