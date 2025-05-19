require_relative '../../lib/smart_app_launch/token_refresh_test'

RSpec.describe SMARTAppLaunch::TokenRefreshBodyTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_token_refresh_body') }
  let(:requests_repo) { Inferno::Repositories::Requests.new }
  let(:suite_id) { 'smart'}
  let(:token_url) { 'http://example.com/fhir/token' }
  let(:refresh_token) { 'REFRESH_TOKEN' }
  let(:received_scopes) { 'openid profile launch offline_access patient/*.*' }
  let(:valid_body) do
    {
      access_token: 'ACCESS_TOKEN2',
      token_type: 'bearer',
      expires_in: 3600,
      scope: received_scopes,
      refresh_token: 'REFRESH_TOKEN2'
    }
  end

  def create_token_refresh_request(body: nil, status: 200, headers: nil)
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
      name: 'token_refresh',
      url: 'http://example.com/token',
      test_session_id: test_session.id,
      response_body: body.is_a?(Hash) ? body.to_json : body,
      status: status,
      headers: headers
    )
  end

  it 'passes if the body contains the required fields' do
    create_token_refresh_request(body: valid_body)

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('pass')
  end

  it 'fails if the body is invalid json' do
    create_token_refresh_request(body: '[[')

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Invalid JSON/)
  end

  it 'fails if a required field is missing' do
    required_fields = ['access_token', 'token_type', 'expires_in', 'scope']
    required_fields.each do |field|
      body = valid_body.dup
      body.delete(field.to_sym)
      create_token_refresh_request(body: body)

      result = run(test, received_scopes: received_scopes)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/#{field}/)
    end
  end

  it 'fails if token_type is not bearer' do
    body = valid_body
    body[:token_type] = 'abc'
    create_token_refresh_request(body: body)

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/bearer/)
  end

  it 'fails if scopes are not a subset of the original scopes' do
    body = valid_body
    body[:scope] += ' user/*.*'
    create_token_refresh_request(body: body)

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/contained scopes which are not a subset/)
  end

  it 'passes if the scopes are a subset of the original scopes' do
    body = valid_body
    body[:scope] = body[:scope].split
    body[:scope].pop
    body[:scope] = body[:scope].join(' ')
    create_token_refresh_request(body: body)

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('pass')
  end

  it 'fails is the fields are the wrong types' do
    described_class::STRING_FIELDS.each do |field|
      body = valid_body.merge(field => 123)
      create_token_refresh_request(body: body)

      result = run(test, received_scopes: received_scopes)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/String/)
    end

    described_class::NUMERIC_FIELDS.each do |field|
      body = valid_body.merge(field => '123')
      create_token_refresh_request(body: body)

      result = run(test, received_scopes: received_scopes)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match(/Numeric/)
    end
  end

  it 'persists outputs' do
    create_token_refresh_request(body: valid_body)

    result = run(test, received_scopes: received_scopes)

    expect(result.result).to eq('pass')
    persisted_refresh_token =
      session_data_repo.load(test_session_id: test_session.id, name: :refresh_token)
    persisted_access_token =
      session_data_repo.load(test_session_id: test_session.id, name: :access_token)
    persisted_token_retrieval_time =
      session_data_repo.load(test_session_id: test_session.id, name: :token_retrieval_time)
    persisted_expires_in =
      session_data_repo.load(test_session_id: test_session.id, name: :expires_in)
    persisted_received_scopes =
      session_data_repo.load(test_session_id: test_session.id, name: :received_scopes)

    expect(persisted_refresh_token).to eq(valid_body[:refresh_token])
    expect(persisted_access_token).to eq(valid_body[:access_token])
    expect(persisted_expires_in).to eq(valid_body[:expires_in].to_s)
    expect(persisted_received_scopes).to eq(valid_body[:scope])
    expect(persisted_token_retrieval_time).to be_present
    expect { Date.parse(persisted_token_retrieval_time) }.to_not raise_error
  end
end
