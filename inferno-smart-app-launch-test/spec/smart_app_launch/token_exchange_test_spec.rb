require_relative '../../lib/smart_app_launch/token_exchange_test'

RSpec.describe SMARTAppLaunch::TokenExchangeTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_exchange') }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }
  let(:token_url) { 'http://example.com/token' }
  let(:redirect_uri) { "#{Inferno::Application['base_url']}/custom/smart/redirect" }
  let(:public_inputs) do
    {
      code: 'CODE',
      smart_auth_info: Inferno::DSL::AuthInfo.new(
        client_id: 'CLIENT_ID',
        pkce_support: 'disabled',
        token_url:
      )
    }
  end
  let(:confidential_inputs) do
    public_inputs[:smart_auth_info].client_secret = 'CLIENT_SECRET'
    public_inputs[:smart_auth_info].auth_type = 'symmetric'
    public_inputs
  end

  def create_redirect_request(url)
    repo_create(
      :request,
      direction: 'incoming',
      name: 'redirect',
      url: url,
      test_session_id: test_session.id
    )
  end

  context 'with a confidential client' do
    it 'passes if the token response has a 200 status' do
      create_redirect_request('http://example.com/redirect?code=CODE')
      stub_request(:post, token_url)
        .with(
          body:
            {
              grant_type: 'authorization_code',
              code: 'CODE',
              redirect_uri: "#{Inferno::Application['base_url']}/custom/smart/redirect"
            },
          headers: { 'Authorization' => "Basic #{Base64.strict_encode64('CLIENT_ID:CLIENT_SECRET')}" }
        )
        .to_return(status: 200, body: {}.to_json)

      result = run(test, confidential_inputs)

      expect(result.result).to eq('pass')
    end
  end

  context 'with a public client' do
    it 'passes if the token response has a 200 status' do
      create_redirect_request('http://example.com/redirect?code=CODE')
      stub_request(:post, token_url)
        .with(
          body:
            {
              grant_type: 'authorization_code',
              code: 'CODE',
              client_id: 'CLIENT_ID',
              redirect_uri:
            }
        )
        .to_return(status: 200, body: {}.to_json)

      result = run(test, public_inputs)

      expect(result.result).to eq('pass')
    end
  end

  it 'fails if a non-200 response is received' do
    create_redirect_request('http://example.com/redirect?code=CODE')
    stub_request(:post, token_url)
      .with(
        body:
          {
            grant_type: 'authorization_code',
            code: 'CODE',
            client_id: 'CLIENT_ID',
            redirect_uri:
          }
      )
      .to_return(status: 201)

    result = run(test, public_inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Unexpected response status/)
  end

  it 'skips if the auth request had an error' do
    create_redirect_request('http://example.com/redirect?code=CODE&error=invalid_request')

    result = run(test, public_inputs)

    expect(result.result).to eq('skip')
    expect(result.result_message).to eq('Error during authorization request')
  end

  context 'with PKCE support' do
    it 'sends the code verifier' do
      create_redirect_request('http://example.com/redirect?code=CODE')
      token_request =
        stub_request(:post, token_url)
          .with(
            body:
              {
                grant_type: 'authorization_code',
                code: 'CODE',
                client_id: 'CLIENT_ID',
                redirect_uri:,
                code_verifier: 'CODE_VERIFIER'
              }
          )
          .to_return(status: 200, body: {}.to_json)

      public_inputs[:smart_auth_info].pkce_support = 'enabled'
      public_inputs[:pkce_code_verifier] = 'CODE_VERIFIER'
      result = run(test, public_inputs)

      expect(result.result).to eq('pass')
      expect(token_request).to have_been_made
    end
  end
end
