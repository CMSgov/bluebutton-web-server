require_relative '../../lib/smart_app_launch/openid_token_header_test'

RSpec.describe SMARTAppLaunch::OpenIDTokenHeaderTest do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_openid_token_header') }
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
  let(:rsa_keys) { [jwk.export] }
  let(:id_token) { JWT.encode(payload, key_pair, 'RS256', kid: jwk.kid) }
  let(:header) { JWT.decode(id_token, nil, false)[1] }

  it 'skips if no id token header is available' do
    result = run(test, id_token_header_json: nil)

    expect(result.result).to eq('skip')
  end

  it 'skips if no rsa keys are available' do
    result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: '')

    expect(result.result).to eq('skip')
  end

  it 'passes when the and the keys match' do
    result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_keys.to_json)

    expect(result.result).to eq('pass')
  end

  it 'fails if the token was not signed with RS256' do
    header['alg'] = 'abc'
    result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_keys.to_json)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/ID Token signed with `abc`/)
  end

  context 'when one key is present' do
    it 'fails if the kid does not match' do
      header['kid'] = 'KID'
      result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_keys.to_json)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/with an id of `#{header['kid']}`/)
    end
  end

  context 'when multiple keys are present' do
    let(:rsa_multiple_keys) { rsa_keys << JWT::JWK.new(OpenSSL::PKey::RSA.new(2048)).export }

    it 'fails if the kid field is not present' do
      header.delete 'kid'
      result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_multiple_keys.to_json)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/`kid` field must be present/)
    end

    it 'fails if the kid does not match a key' do
      header['kid'] = 'KID'
      result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_multiple_keys.to_json)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/with an id of `#{header['kid']}`/)
    end
  end

  it 'persists outputs' do
    result = run(test, id_token_header_json: header.to_json, openid_rsa_keys_json: rsa_keys.to_json)

    expect(result.result).to eq('pass')

    persisted_header = session_data_repo.load(test_session_id: test_session.id, name: :id_token_header_json)
    expect(persisted_header).to eq(header.to_json)

    persisted_keys = session_data_repo.load(test_session_id: test_session.id, name: :openid_rsa_keys_json)
    expect(persisted_keys).to eq(rsa_keys.to_json)
  end
end
