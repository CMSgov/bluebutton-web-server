require_relative '../../lib/smart_app_launch/token_exchange_stu2_test'

RSpec.describe SMARTAppLaunch::TokenExchangeSTU2Test, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_exchange_stu2') }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }
  let(:token_url) { 'http://example.com/token' }
  let(:client_id) { 'CLIENT_ID' }
  let(:inputs) do
    {
      code: 'CODE',
      smart_auth_info: Inferno::DSL::AuthInfo.new(
        auth_type: 'asymmetric',
        client_id:,
        pkce_support: 'disabled',
        encryption_algorithm: 'ES384',
        token_url:
      )
    }
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

  context 'with an asymmetric confidential client' do
    it 'passes if the token response has a 200 status' do
      create_redirect_request('http://example.com/redirect?code=CODE')
      stub_request(:post, token_url)
        .with(
          body: hash_including(
            {
              grant_type: 'authorization_code',
              code: 'CODE',
              redirect_uri: "#{Inferno::Application['base_url']}/custom/smart/redirect",
              client_assertion_type: 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
            }
          )
        )
        .to_return(status: 200, body: {}.to_json)

      result = run(test, inputs)

      expect(result.result).to eq('pass')
    end
  end
end
