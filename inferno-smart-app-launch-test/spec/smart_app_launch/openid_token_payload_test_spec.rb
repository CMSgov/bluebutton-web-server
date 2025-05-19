require_relative '../../lib/smart_app_launch/openid_token_payload_test'

RSpec.describe SMARTAppLaunch::OpenIDTokenPayloadTest do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_openid_token_payload') }
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
  let(:inputs) do
    {
      id_token: id_token,
      openid_configuration_json: config.to_json,
      id_token_jwk_json: jwk.export.to_json,
      smart_auth_info: Inferno::DSL::AuthInfo.new(client_id:)
    }
  end

  it 'skips if no id token is available' do
    inputs[:id_token] = nil
    result = run(test, inputs)

    expect(result.result).to eq('skip')
  end

  it 'skips if no openid configuration is available' do
    inputs[:openid_configuration_json] = nil
    result = run(test, inputs)

    expect(result.result).to eq('skip')
  end

  it 'skips if no jwk is available' do
    inputs[:id_token_jwk_json] = nil
    result = run(test, inputs)

    expect(result.result).to eq('skip')
  end

  it 'skips if no client id is available' do
    inputs[:smart_auth_info].client_id = nil
    result = run(test, inputs)

    expect(result.result).to eq('skip')
  end

  it 'passes when the id token is valid' do
    result = run(test, inputs)

    expect(result.result).to eq('pass')
  end

  it 'fails if the iss does not match the issuer from the configuration' do
    config[:issuer] += 'abc'
    inputs[:openid_configuration_json] = config.to_json
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/issuer/)
  end

  it 'fails if the aud does not match the client id' do
    inputs[:smart_auth_info].client_id = "#{client_id}abc"
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/aud/)
  end

  it 'fails if the exp does not represent a time in the future' do
    payload[:exp] = 1.hour.ago.to_i
    token = JWT.encode(payload, key_pair, 'RS256', kid: jwk.kid)
    inputs[:id_token] = token
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/exp/)
  end

  it 'fails if the sub is blank' do
    payload[:sub] = ' '
    token = JWT.encode(payload, key_pair, 'RS256', kid: jwk.kid)
    inputs[:id_token] = token
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match('ID token `sub` claim is blank')
  end

  it 'fails if the sub exceeds 255 characters' do
    payload[:sub] = '0' * 256
    token = JWT.encode(payload, key_pair, 'RS256', kid: jwk.kid)
    inputs[:id_token] = token
    result = run(test, inputs)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match('ID token `sub` claim exceeds 255 characters in length')
  end

  it 'fails if any required fields are missing' do
    test::REQUIRED_CLAIMS.each do |claim|
      bad_payload = payload.dup
      bad_payload.delete(claim.to_sym)
      token = JWT.encode(bad_payload, key_pair, 'RS256', kid: jwk.kid)

      inputs[:id_token] = token
      result = run(test, inputs)

      expect(result.result).to eq('fail')
      expect(result.result_message).to include(claim)
    end
  end
end
