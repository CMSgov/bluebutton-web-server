require_relative '../../lib/smart_app_launch/token_refresh_stu2_test'

RSpec.describe SMARTAppLaunch::TokenRefreshSTU2Test, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_refresh_stu2') }
  let(:requests_repo) { Inferno::Repositories::Requests.new }
  let(:suite_id) { 'smart'}
  let(:token_url) { 'http://example.com/fhir/token' }
  let(:refresh_token) { 'REFRESH_TOKEN' }
  let(:client_id) { 'CLIENT_ID' }
  let(:client_secret) { 'CLIENT_SECRET' }
  let(:received_scopes) { 'openid profile launch offline_access patient/*.*' }
  let(:valid_response) do
    {
      access_token: 'ACCESS_TOKEN',
      token_type: 'Bearer',
      expires_in: 3600,
      scope: received_scopes,
      refresh_token: 'REFRESH_TOKEN2'
    }
  end

  it 'skips if no refresh_token is available' do
    result = run(test, refresh_token: nil)

    expect(result.result).to eq('skip')
  end

  context 'with a public client' do
    let(:auth_type) { 'public' }

    it 'passes when the refresh succeeds' do
      stub_request(:post, token_url)
        .to_return(
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: valid_response.to_json
        )

      result = run(
        test,
        received_scopes:,
        smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, auth_type:, refresh_token:, token_url:)
      )

      expect(result.result).to eq('pass')
    end
  end

  context 'with a confidential symmetric client' do
    let(:auth_type) { 'symmetric' }

    it 'passes when the refresh succeeds' do
      credentials = Base64.strict_encode64("#{client_id}:#{client_secret}")
      stub_request(:post, token_url)
        .with(
          headers: {
            Authorization: "Basic #{credentials}"
          }
        )
        .to_return(
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: valid_response.to_json
        )

      inputs = {
        received_scopes:,
        smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, client_secret:, auth_type:, refresh_token:, token_url:)
      }
      result = run(test, inputs)
      expect(result.result).to eq('pass')
    end
  end

  context 'with a confidential asymmetric client' do
    let(:auth_type) { 'asymmetric' }
    let(:encryption_algorithm) { 'RS384' }

    it 'passes when the refresh succeeds' do
      stub_request(:post, token_url)
        .to_return(
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: valid_response.to_json
        )

      result = run(
        test,
        received_scopes:,
        smart_auth_info: Inferno::DSL::AuthInfo.new(
          client_id:, auth_type:, encryption_algorithm:, refresh_token:, token_url:
        )
      )

      expect(result.result).to eq('pass')
    end
  end

  it 'fails if a non-200/201 response is received' do
    stub_request(:post, token_url)
      .to_return(
        status: 202,
        headers: {
          'Content-Type': 'application/json'
        },
        body: valid_response.to_json
      )

    result = run(
      test,
      received_scopes:,
      smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, auth_type: 'public', refresh_token:, token_url:)
    )

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/202/)
  end

  it 'fails if a non-json response is received' do
    stub_request(:post, token_url)
      .to_return(
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        },
        body: '[['
      )

    result = run(
      test,
      received_scopes:,
      smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, auth_type: 'public', refresh_token:, token_url:)
    )

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JSON/)
  end

  it 'persists request' do
    stub_request(:post, token_url)
      .to_return(
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        },
        body: valid_response.to_json
      )

    result = run(
      test,
      received_scopes:,
      smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, auth_type: 'public', refresh_token:, token_url:)
    )

    expect(result.result).to eq('pass')

    request = requests_repo.find_named_request(test_session.id, :token_refresh)
    expect(request).to be_present
  end

  context 'when the response does not contain a refresh token' do
    it 'includes the original refresh token in the smart credentials' do
      stub_request(:post, token_url)
        .to_return(
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: valid_response.except(:refresh_token).to_json
        )

      result = run(
        test,
        received_scopes:,
        smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:, auth_type: 'public', refresh_token:, token_url:)
      )

      expect(result.result).to eq('pass')

      smart_credentials =
        JSON.parse(
          session_data_repo.load(
            test_session_id: test_session.id,
            name: :smart_credentials
          )
        ).symbolize_keys

      expect(smart_credentials[:refresh_token]).to eq(refresh_token)
    end
  end
end
