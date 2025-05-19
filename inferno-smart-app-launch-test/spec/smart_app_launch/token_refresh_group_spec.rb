require_relative '../../lib/smart_app_launch/token_refresh_group'

RSpec.describe SMARTAppLaunch::TokenRefreshGroup, :request do
  let(:suite_id) { 'smart' }
  let(:group) { Inferno::Repositories::TestGroups.new.find('smart_token_refresh') }
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:requests_repo) { Inferno::Repositories::Requests.new }
  let(:url) { 'http://example.com/fhir' }
  let(:token_url) { "#{url}/token" }
  let(:inputs) do
    {
      smart_auth_info: Inferno::DSL::AuthInfo.new(
        client_id: 'CLIENT_ID',
        refresh_token: 'REFRESH_TOKEN',
        token_url:
      ),
      received_scopes: 'launch/patient patient/*.*'
    }
  end
  let(:token_response) do
    {
      access_token: 'ACCESS_TOKEN',
      id_token: 'ID_TOKEN',
      refresh_token: 'REFRESH_TOKEN2',
      expires_in: 3600,
      patient: '123',
      encounter: '456',
      scope: 'launch/patient patient/*.*',
      intent: 'INTENT',
      token_type: 'Bearer'
    }
  end
  let(:token_response_headers) do
    {
      'Cache-Control' => 'no-store',
      'Pragma' => 'no-cache'
    }
  end

  it 'persists requests and outputs' do
    stub_request(:post, token_url)
      .to_return(status: 200, body: token_response.to_json, headers: token_response_headers)
    run(group, inputs)

    state = session_data_repo.load(test_session_id: test_session.id, name: 'standalone_state')
    get "/custom/smart/redirect?state=#{state}&code=CODE"

    results = results_repo.current_results_for_test_session(test_session.id)

    expect(results.map(&:result)).to all(eq('pass'))

    expected_outputs = {
      access_token: token_response[:access_token],
      refresh_token: token_response[:refresh_token],
      expires_in: token_response[:expires_in],
      received_scopes: token_response[:scope]
    }
    other_outputs = [:token_retrieval_time]

    expected_outputs.each do |name, value|
      expect(session_data_repo.load(test_session_id: test_session.id, name: name)).to eq(value.to_s)
    end

    other_outputs.each do |name|
      expect(session_data_repo.load(test_session_id: test_session.id, name: name)).to be_present
    end

    expect(requests_repo.find_named_request(test_session.id, 'token_refresh')).to be_present
  end
end
