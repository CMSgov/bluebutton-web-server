require_relative '../../lib/smart_app_launch/code_received_test'

RSpec.describe SMARTAppLaunch::CodeReceivedTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_code_received') }
  let(:suite_id) { 'smart'}

  def create_redirect_request(url)
    repo_create(
      :request,
      direction: 'incoming',
      name: 'redirect',
      url: url,
      test_session_id: test_session.id
    )
  end

  it 'passes if it receives a code with no error' do
    create_redirect_request('http://example.com/redirect?code=CODE')
    result = run(test)

    expect(result.result).to eq('pass')
  end

  it 'fails if it receives an error' do
    create_redirect_request('http://example.com/redirect?code=CODE&error=invalid_request')
    result = run(test)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Error returned from authorization server/)
    expect(result.result_message).to include('invalid_request')
  end

  it 'includes the error description and uri in the failure message if present' do
    create_redirect_request(
      'http://example.com/redirect?code=CODE&error=invalid_request&error_description=DESCRIPTION&error_uri=URI'
    )
    result = run(test)

    expect(result.result).to eq('fail')
    expect(result.result_message).to match(/Error returned from authorization server/)
    expect(result.result_message).to include('DESCRIPTION')
    expect(result.result_message).to include('URI')
  end
end
