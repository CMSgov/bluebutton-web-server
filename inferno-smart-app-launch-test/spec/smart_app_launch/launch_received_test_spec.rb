require_relative '../../lib/smart_app_launch/launch_received_test'

RSpec.describe SMARTAppLaunch::LaunchReceivedTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_launch_received') }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }

  it 'outputs the launch parameter' do
    repo_create(
      :request,
      name: 'launch',
      url: "http://example.com/?launch=#{url}",
      test_session_id: test_session.id
    )

    result = run(test)

    expect(result.result).to eq('pass')

    launch = session_data_repo.load(test_session_id: test_session.id, name: :launch)

    expect(launch).to eq(url)
  end
end
