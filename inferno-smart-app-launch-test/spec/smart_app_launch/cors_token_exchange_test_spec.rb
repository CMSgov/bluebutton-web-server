require_relative '../../lib/smart_app_launch/cors_token_exchange_test'

RSpec.describe SMARTAppLaunch::CORSTokenExchangeTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_cors_token_exchange') }
  let(:suite_id) { 'smart'}

  let(:valid_body) do
    {
      access_token: 'ACCESS_TOKEN',
      token_type: 'bearer',
      expires_in: 3600,
      scope: 'patient/*.*'
    }
  end

  let(:inputs) do
    { smart_auth_info: Inferno::DSL::AuthInfo.new(auth_type: 'public') }
  end

  def cors_header_origin(value)
    [
      {
        type: 'response',
        name: 'Access-Control-Allow-Origin',
        value:
      }
    ]
  end

  def create_cors_token_request(body: nil, status: 200, headers: nil)
    repo_create(
      :request,
      direction: 'outgoing',
      name: 'cors_token_request',
      url: 'http://example.com/token',
      test_session_id: test_session.id,
      response_body: body.is_a?(Hash) ? body.to_json : body,
      status:,
      headers:
    )
  end

  it 'passes if the token request contains a valid cors header with Inferno Origin' do
    create_cors_token_request(body: valid_body, headers: cors_header_origin(Inferno::Application['inferno_host']))

    result = run(test, inputs)
    expect(result.result).to eq('pass')
  end

  it 'passes if the token request contains a valid wildcard cors header' do
    create_cors_token_request(body: valid_body, headers: cors_header_origin('*'))

    result = run(test, inputs)

    expect(result.result).to eq('pass')
  end

  it 'skips if the previous token request was not made' do
    result = run(test, inputs)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/was not made/)
  end

  it 'omits if the client auth type is not public' do
    create_cors_token_request(body: valid_body, headers: cors_header_origin('*'))

    inputs[:smart_auth_info].auth_type = 'symmetric'
    result = run(test, inputs)

    expect(result.result).to eq('omit')
    expect(result.result_message).to match(/Client type is not public/)
  end

  it 'fails if the CORS header is not included in response' do
    create_cors_token_request(body: valid_body, headers: [])

    result = run(test, inputs)
    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Request must have `Access-Control-Allow-Origin`/)
  end

  it 'fails if the CORS header is not valid' do
    create_cors_token_request(body: valid_body, headers: cors_header_origin('incorrect_origin'))

    result = run(test, inputs)
    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Request must have `Access-Control-Allow-Origin`/)
  end
end
