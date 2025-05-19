RSpec.describe SMARTAppLaunch::SMARTClientAppLaunchAuthorizationRequestVerification do # rubocop:disable RSpec/SpecFilePathFormat
  include SMARTAppLaunch::URLs
  let(:suite_id) { 'smart_client_stu2_2' }
  let(:test) { described_class }
  let(:test_session) do # overriden to add suite options
    repo_create(
      :test_session,
      suite: suite_id,
      suite_options: [Inferno::DSL::SuiteOption.new(
        id: :client_type,
        value: SMARTAppLaunch::SMARTClientOptions::SMART_APP_LAUNCH_PUBLIC
      )]
    )
  end
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:dummy_result) { repo_create(:result, test_session_id: test_session.id) }
  let(:client_id) { 'sample_client' }
  let(:authorization_url) { client_authorization_url }
  let(:authorization_code) { SMARTAppLaunch::MockSMARTServer.client_id_to_token(client_id, 5) }
  let(:redirect_uri) { 'https://inferno.healthit.gov/redirect' }

  def create_authorization_request(body, authorization_code)
    headers ||= [
      {
        type: 'response',
        name: 'Location',
        value: "#{redirect_uri}?code=#{authorization_code}"
      }
    ]
    repo_create(
      :request,
      direction: 'incoming',
      url: "#{authorization_url}?#{Rack::Utils.build_query(body)}",
      result: dummy_result,
      test_session_id: test_session.id,
      status: 302,
      headers:,
      verb: 'get',
      tags: [SMARTAppLaunch::AUTHORIZATION_TAG, SMARTAppLaunch::SMART_TAG,
             SMARTAppLaunch::AUTHORIZATION_CODE_TAG]
    )
  end

  it 'skips if no authorization requests' do
    result = run(test, client_id:, smart_redirect_uris: redirect_uri)
    expect(result.result).to eq('skip')
    expect(result.result_message).to eq('No SMART authorization requests made.')
  end

  it 'passes for a valid authorization request' do
    body = { 
      response_type: 'code', 
      client_id:,
      redirect_uri:,
      state: 'test',
      aud: client_fhir_base_url,
      code_challenge: 'dummy',
      code_challenge_method: 'S256',
      scope: 'system/*.rs'
    }
    create_authorization_request(body, authorization_code)
    result = run(test, client_id:, smart_redirect_uris: redirect_uri)
    expect(result.result).to eq('pass')
  end

  it 'fails for an invalid authorization request' do
    create_authorization_request({ client_id: }, authorization_code)
    result = run(test, client_id:, smart_redirect_uris: redirect_uri)
    expect(result.result).to eq('fail')
  end
end
