require_relative '../../lib/smart_app_launch/openid_connect_group'

RSpec.describe SMARTAppLaunch::OpenIDConnectGroup do
  let(:group) { Inferno::Repositories::TestGroups.new.find('smart_openid_connect') }
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }
  let(:client_id) { 'CLIENT_ID' }
  let(:payload) do
    {
      iss: url,
      exp: 1.hour.from_now.to_i,
      nbf: Time.now.to_i,
      iat: Time.now.to_i,
      aud: client_id,
      sub: SecureRandom.uuid,
      fhirUser: "#{url}/Patient/123"
    }
  end
  let(:key_pair) { OpenSSL::PKey::RSA.new(2048) }
  let(:jwk) { JWT::JWK.new(key_pair) }
  let(:id_token) { JWT.encode(payload, key_pair, 'RS256', kid: jwk.kid) }
  let(:config) do
    {
      registration_endpoint: 'https://www.example.com/register',
      token_endpoint: 'https://www.example.com/token',
      token_endpoint_auth_methods_supported: %w[client_secret_post client_secret_basic none],
      jwks_uri: 'https://www.example.com/jwk',
      id_token_signing_alg_values_supported: %w[HS256 HS384 HS512 RS256 RS384 RS512 none],
      authorization_endpoint: 'https://www.example.com/authorize',
      introspection_endpoint: 'https://www.example.com/introspect',
      response_types_supported: ['code'],
      grant_types_supported: ['authorization_code'],
      scopes_supported: ['launch', 'openid', 'patient/*.*', 'profile'],
      userinfo_endpoint: 'https://www.example.com/userinfo',
      issuer: url,
      subject_types_supported: 'public'
    }
  end

  it 'passes' do
    stub_request(:get, config[:jwks_uri])
      .to_return(
        status: 200,
        body: { keys: [jwk.export] }.to_json
      )
    stub_request(:get, "#{url}/.well-known/openid-configuration")
      .to_return(
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        },
        body: config.to_json
      )
    stub_request(:get, payload[:fhirUser])
      .to_return(status: 200, body: FHIR::Patient.new(id: '123').to_json)

    inputs = {
      id_token: id_token,
      url: url,
      smart_auth_info: Inferno::DSL::AuthInfo.new(
        client_id:,
        requested_scopes: 'openid fhirUser'
      )
    }

    run(group, inputs)
    results = results_repo.current_results_for_test_session(test_session.id)

    expect(results.map(&:result)).to all(eq('pass'))
  end
end
