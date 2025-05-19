RSpec.describe SMARTAppLaunch::SMARTClientRegistrationAppLaunchConfidentialAsymmetricVerification, :request do # rubocop:disable RSpec/SpecFilePathFormat
  let(:suite_id) { 'smart_client_stu2_2' }
  let(:static_uuid) { 'f015a331-3a86-4566-b72f-b5b85902cdca' }
  let(:test) { described_class }
  let(:test_session) do # overriden to add suite options
    repo_create(
      :test_session,
      suite: suite_id,
      suite_options: [Inferno::DSL::SuiteOption.new(
        id: :client_type,
        value: SMARTAppLaunch::SMARTClientOptions::SMART_APP_LAUNCH_CONFIDENTIAL_ASYMMETRIC
      )]
    )
  end
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:requests_repo) { Inferno::Repositories::Requests.new }
  let(:client_id) { 'test_client' }
  let(:redirect_uri) { "https://inferno.healthit.gov/redirect"}
  let(:launch_url) { "https://inferno.healthit.gov/launch"}
  let(:not_https) { "http://inferno.healthit.gov/dummy"}
  let(:jwks_valid) do
    File.read(File.join(__dir__, '..', '..', '..', 'lib', 'smart_app_launch', 'smart_jwks.json'))
  end
  
  it 'it succeeds for valid inputs' do
    inputs = { client_id:, smart_jwk_set: jwks_valid, smart_redirect_uris: redirect_uri, smart_launch_urls: launch_url}
    result = run(test, inputs)
    expect(result.result).to eq('pass')
  end

  it 'it fails for invalid inputs' do
    inputs = { client_id:, smart_jwk_set: jwks_valid, smart_redirect_uris: 'bad', smart_launch_urls: launch_url}
    result = run(test, inputs)
    expect(result.result).to eq('fail')
  end

  it 'it defaults the client id to the session if not provided' do
    inputs = { smart_jwk_set: jwks_valid, smart_redirect_uris: redirect_uri, smart_launch_urls: launch_url}
    result = run(test, inputs)
    expect(result.result).to eq('pass')
    defaulted_client_id = JSON.parse(result.output_json).find { |output| output['name'] == 'client_id' }&.dig('value')
    expect(defaulted_client_id).to eq(test_session.id)
  end

  it 'it normalizes uri and url lists and returns the valid ones' do
    uri_mix = "    bad,,,  #{not_https}\n,#{redirect_uri}\n\n,,,bad,"
    expected_normalized_uris = "#{not_https},#{redirect_uri}"
    url_mix = "#{redirect_uri}    bad,,,  #{not_https}\n,,,,bad,#{launch_url}"
    expected_normalized_urls = "#{not_https},#{launch_url}"
    inputs = { smart_jwk_set: jwks_valid, smart_redirect_uris: uri_mix, smart_launch_urls: url_mix}
    result = run(test, inputs)
    expect(result.result).to eq('fail')

    normalized_urli = JSON.parse(result.output_json).find { |output| output['name'] == 'smart_redirect_uris' }&.dig('value')
    expect(normalized_urli).to eq(expected_normalized_uris)
    normalized_urls = JSON.parse(result.output_json).find { |output| output['name'] == 'smart_launch_urls' }&.dig('value')
    expect(normalized_urls).to eq(expected_normalized_urls)
  end
end
