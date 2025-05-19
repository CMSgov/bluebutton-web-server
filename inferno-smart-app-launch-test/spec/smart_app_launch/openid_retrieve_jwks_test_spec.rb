require_relative '../../lib/smart_app_launch/openid_retrieve_jwks_test'

RSpec.describe SMARTAppLaunch::OpenIDRetrieveJWKSTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_openid_retrieve_jwks') }
  let(:requests_repo) { Inferno::Repositories::Requests.new }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }
  let(:key_pair) { OpenSSL::PKey::RSA.new(2048) }
  let(:jwk) { JWT::JWK.new(key_pair) }

  it 'skips if no jwks uri is available' do
    result = run(test, openid_jwks_uri: nil)

    expect(result.result).to eq('skip')
  end

  it 'passes when the jwks can be retrieved' do
    stub_request(:get, url)
      .to_return(
        status: 200,
        body: { keys: [jwk.export] }.to_json
      )
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('pass')
  end

  it 'persists outputs and requests' do
    body = { keys: [jwk.export] }.to_json
    stub_request(:get, url)
      .to_return(
        status: 200,
        body: body
      )
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('pass')

    persisted_jwks = session_data_repo.load(test_session_id: test_session.id, name: :openid_jwks_json)
    expect(persisted_jwks).to eq(body)

    persisted_rsa_keys = session_data_repo.load(test_session_id: test_session.id, name: :openid_rsa_keys_json)
    expect(persisted_rsa_keys).to eq([jwk.export].to_json)

    request = requests_repo.find_named_request(test_session.id, :openid_jwks)
    expect(request).to be_present
  end

  it 'fails if a non-200 response is received' do
    stub_request(:get, url)
      .to_return(status: 201)
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/201/)
  end

  it 'fails if the response body is not valid json' do
    stub_request(:get, url)
      .to_return(status: 200, body: 'xyz')
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JSON/)
  end

  it 'fails if the `keys` field is not an array' do
    stub_request(:get, url)
      .to_return(status: 200, body: { keys: 'xyz' }.to_json)
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/must be an array/)
  end

  it 'fails if the `keys` field contains no RSA keys' do
    stub_request(:get, url)
      .to_return(status: 200, body: { keys: [{ kty: 'xyz' }] }.to_json)
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/JWKS contains no RSA keys/)
  end

  it 'fails if an invalid key is present' do
    stub_request(:get, url)
      .to_return(status: 200, body: { keys: [{ kty: 'RSA' }] }.to_json)
    result = run(test, openid_jwks_uri: url)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JWK:/)
  end
end
