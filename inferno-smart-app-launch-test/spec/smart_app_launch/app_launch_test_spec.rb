require_relative '../../lib/smart_app_launch/app_launch_test'

RSpec.describe SMARTAppLaunch::AppLaunchTest, :request do
  let(:test) { Inferno::Repositories::Tests.new.find('smart_app_launch') }
  let(:results_repo) { Inferno::Repositories::Results.new }
  let(:suite_id) { 'smart'}
  let(:url) { 'http://example.com/fhir' }

  it 'passes when a request is received with the provided url' do
    allow(test).to receive(:parent).and_return(Inferno::TestGroup)
    result = run(test, url: url)

    expect(result.result).to eq('wait')

    get "/custom/smart/launch?iss=#{url}"

    result = results_repo.find(result.id)

    expect(result.result).to eq('pass')
  end
end
