require_relative '../../lib/smart_app_launch/smart_access_brands_retrieve_bundle_test'

RSpec.describe SMARTAppLaunch::SMARTAccessBrandsRetrievalTest do
  let(:suite_id) { 'smart_access_brands' }
  let(:results_repo) { Inferno::Repositories::Results.new }

  let(:smart_access_brands_bundle) do
    JSON.parse(File.read(File.join(
                           __dir__, '..', 'fixtures', 'smart_access_brands_example.json'
                         )))
  end

  let(:user_access_brands_publication_url) { 'http://fhirserver.org/smart_access_brands_example.json' }

  let(:headers) do
    { 'Content-Type' => 'application/json',
      'Access-Control-Allow-Origin' => '*',
      'Etag' => SecureRandom.hex(32) }
  end

  def entity_result_message(runnable)
    results_repo.current_results_for_test_session_and_runnables(test_session.id, [runnable])
      .first
      .messages
      .map(&:message)
      .join(' ')
  end

  def entity_result_message_type(runnable)
    results_repo.current_results_for_test_session_and_runnables(test_session.id, [runnable])
      .first
      .messages
      .map(&:type)
      .first
  end

  describe 'Receive SMART Access Brands Bundle Test' do
    let(:test) do
      Class.new(SMARTAppLaunch::SMARTAccessBrandsRetrievalTest) do
        http_client do
          url :user_access_brands_publication_url
          headers Accept: 'application/json, application/fhir+json'
        end

        input :user_access_brands_publication_url
      end
    end

    it 'passes if successfully retrieves user-Access Brands Bundle' do
      user_access_brands_request = stub_request(:get, user_access_brands_publication_url)
        .to_return(status: 200, headers:, body: smart_access_brands_bundle.to_json)

      result = run(test, user_access_brands_publication_url:)

      expect(result.result).to eq('pass')
      expect(user_access_brands_request).to have_been_made
    end

    it 'skips if no user-Access Brands Bundle URL inputted' do
      result = run(test)

      expect(result.result).to eq('skip')
      expect(result.result_message).to match('No User Access Brands Publication endpoint URL inputted')
    end

    it 'fails if retrieving user-Access Brands Bundle returns non 200' do
      user_access_brands_request = stub_request(:get, user_access_brands_publication_url)
        .to_return(status: 404)

      result = run(test, user_access_brands_publication_url:)

      expect(result.result).to eq('fail')
      expect(result.result_message).to eq('Unexpected response status: expected 200, but received 404')
      expect(user_access_brands_request).to have_been_made
    end

    it 'fails if user-Access Brands Bundle response does not contain CORs header' do
      headers.delete('Access-Control-Allow-Origin')
      user_access_brands_request = stub_request(:get, user_access_brands_publication_url)
        .to_return(status: 200, headers:, body: smart_access_brands_bundle.to_json)

      result = run(test, user_access_brands_publication_url:)

      expect(result.result).to eq('fail')
      expect(result.result_message).to match('All GET requests must support Cross-Origin Resource Sharing')
      expect(user_access_brands_request).to have_been_made
    end

    it 'produces warning if user-Access Brands Bundle response does not contain Etag header' do
      headers.delete('Etag')
      user_access_brands_request = stub_request(:get, user_access_brands_publication_url)
        .to_return(status: 200, headers:, body: smart_access_brands_bundle.to_json)

      result = run(test, user_access_brands_publication_url:)

      expect(result.result).to eq('pass')
      expect(entity_result_message(test)).to match(
        'Brand Bundle HTTP responses should include an Etag header'
      )
      expect(entity_result_message_type(test)).to eq('warning')
      expect(user_access_brands_request).to have_been_made
    end
  end
end
