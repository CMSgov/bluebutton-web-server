require_relative '../../lib/smart_app_launch/token_exchange_test'

RSpec.describe SMARTAppLaunch::TokenResponseHeadersTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_response_headers') }
  let(:suite_id) { 'smart'}

  def create_token_request(body: nil, status: 200, headers: nil)
    headers ||= [
      {
        type: 'response',
        name: 'Cache-Control',
        value: 'no-store'
      },
      {
        type: 'response',
        name: 'Pragma',
        value: 'no-cache'
      }
    ]
    repo_create(
      :request,
      direction: 'outgoing',
      name: 'token',
      url: 'http://example.com/token',
      test_session_id: test_session.id,
      response_body: body.is_a?(Hash) ? body.to_json : body,
      status: status,
      headers: headers
    )
  end

  it 'passes if the response contains headers with the required values' do
    create_token_request

    result = run(test)

    expect(result.result).to eq('pass')
  end

  it 'skips if the token request was not successful' do
    create_token_request(status: 500)

    result = run(test)

    expect(result.result).to eq('skip')
    expect(result.result_message).to match(/was unsuccessful/)
  end

  it 'fails if the required headers are not present' do
    create_token_request(headers: [])

    result = run(test)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Token response must have/)
  end

  it 'fails if the Cache-Control header does not contain no-store' do
    create_token_request(
      headers: [
        {
          type: 'response',
          name: 'Cache-Control',
          value: 'abc'
        },
        {
          type: 'response',
          name: 'Pragma',
          value: 'no-cache'
        }
      ]
    )

    result = run(test)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/`Cache-Control`/)
  end

  it 'fails if the Pragma header does not contain no-cache' do
    create_token_request(
      headers: [
        {
          type: 'response',
          name: 'Cache-Control',
          value: 'no-store'
        },
        {
          type: 'response',
          name: 'Pragma',
          value: 'abc'
        }
      ]
    )

    result = run(test)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/`Pragma`/)
  end
end
